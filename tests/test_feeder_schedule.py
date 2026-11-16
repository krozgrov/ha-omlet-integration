"""Regression tests for feeder schedule validation and failure reporting."""

from datetime import time
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from custom_components.omlet_smart_coop import services


class FeederScheduleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.handlers = {}
        registry = SimpleNamespace(
            async_services=lambda: {},
            has_service=lambda domain, service: False,
            async_register=lambda domain, service, handler: self.handlers.update(
                {service: handler}
            ),
        )
        self.hass = SimpleNamespace(data={}, services=registry)
        self.coordinator = self.make_coordinator()
        await services.async_register_services(self.hass)
        self.handler = self.handlers["update_feeder_schedule"]
        self.targets = patch.object(
            services,
            "_resolve_targets",
            AsyncMock(return_value=[(self.coordinator, ["one", "two"])]),
        )
        self.resolve = self.targets.start()
        self.addCleanup(self.targets.stop)

    def make_coordinator(self):
        return SimpleNamespace(
            api_client=SimpleNamespace(patch_device_configuration=AsyncMock()),
            async_request_refresh=AsyncMock(),
        )

    async def call(self, data):
        await self.handler(SimpleNamespace(data=data))

    async def test_invalid_fields_never_patch_any_target(self):
        cases = [
            {},
            {"time_slot": 1},
            {"feeder_mode": "invalid"},
            {"feeder_mode": None},
        ]
        for field in ("time_slot", "open_light_level", "close_light_level"):
            cases.extend(
                {field: value, "open_time": "06:05"}
                for value in (
                    None,
                    True,
                    False,
                    "oops",
                    1.9,
                    float("nan"),
                    float("inf"),
                    0,
                    5 if field == "time_slot" else 100,
                )
            )
        for field in ("open_time", "close_time"):
            cases.extend(
                {field: value, "feeder_mode": "time"}
                for value in (
                    None,
                    "invalid",
                    "99:99",
                    "24:00",
                    "12:60",
                    42,
                )
            )
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(ServiceValidationError):
                    await self.call(data)
                self.coordinator.api_client.patch_device_configuration.assert_not_awaited()
        self.resolve.assert_not_awaited()

    async def test_valid_settings_are_normalized_and_sent_to_all_targets(self):
        await self.call(
            {
                "time_slot": 4.0,
                "feeder_mode": "time",
                "open_time": time(6, 5),
                "close_time": "17:50:00",
                "open_light_level": 1,
                "close_light_level": 99,
            }
        )
        calls = self.coordinator.api_client.patch_device_configuration.await_args_list
        self.assertEqual([call.args[0] for call in calls], ["one", "two"])
        for call in calls:
            self.assertEqual(
                call.args[1],
                {
                    "feeder": {
                        "mode": "time",
                        "openTime4": "06:05",
                        "closeTime4": "17:50",
                        "openLightLevel": 1,
                        "closeLightLevel": 99,
                    }
                },
            )
        self.coordinator.async_request_refresh.assert_awaited_once()

    async def test_partial_patch_preserves_unsupplied_fields_and_defaults_slot(self):
        await self.call({"open_time": "06:05"})
        self.assertEqual(
            self.coordinator.api_client.patch_device_configuration.await_args.args[1],
            {"feeder": {"openTime1": "06:05"}},
        )

    async def test_api_failure_reports_error_after_attempting_other_targets(self):
        error = RuntimeError("API unavailable")
        self.coordinator.api_client.patch_device_configuration.side_effect = [
            error,
            None,
        ]
        other = self.make_coordinator()
        self.resolve.return_value.append((other, ["three"]))
        with self.assertRaisesRegex(
            HomeAssistantError, "device one: API unavailable"
        ) as ctx:
            await self.call({"open_time": "06:05"})
        self.assertIs(ctx.exception.__cause__, error)
        self.assertEqual(
            self.coordinator.api_client.patch_device_configuration.await_count, 2
        )
        other.api_client.patch_device_configuration.assert_awaited_once()
        self.coordinator.async_request_refresh.assert_awaited_once()
        other.async_request_refresh.assert_awaited_once()

    async def test_all_api_failures_are_reported(self):
        self.coordinator.api_client.patch_device_configuration.side_effect = (
            RuntimeError("offline")
        )
        with self.assertRaises(HomeAssistantError) as ctx:
            await self.call({"feeder_mode": "manual"})
        self.assertIn("device one: offline", str(ctx.exception))
        self.assertIn("device two: offline", str(ctx.exception))

    async def test_refresh_failure_does_not_hide_patch_failure_or_skip_other_accounts(
        self,
    ):
        self.coordinator.api_client.patch_device_configuration.side_effect = [
            RuntimeError("offline"),
            None,
        ]
        self.coordinator.async_request_refresh.side_effect = RuntimeError(
            "refresh failed"
        )
        other = self.make_coordinator()
        self.resolve.return_value.append((other, ["three"]))
        with self.assertRaises(HomeAssistantError) as ctx:
            await self.call({"close_time": "18:00"})
        self.assertIn("device one: offline", str(ctx.exception))
        self.assertIn("refresh failed", str(ctx.exception))
        other.api_client.patch_device_configuration.assert_awaited_once()

    async def test_refresh_failure_is_reported_after_successful_patch(self):
        self.coordinator.async_request_refresh.side_effect = RuntimeError(
            "refresh failed"
        )
        with self.assertRaisesRegex(HomeAssistantError, "refresh failed"):
            await self.call({"close_time": "18:00"})

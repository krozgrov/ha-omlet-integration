# Skill Plan: HA alignment improvements

Goal
- Improve HA best-practice alignment and UX without introducing regressions.

Constraints
- Prefer low-risk changes first.
- Keep changes small and reversible.

Prioritized plan (least impactful -> most impactful)

1) Webhook security alignment (configurable validation)
Goal: Re-enable webhook token validation when a token is configured, while keeping compatibility when it is blank.
Outline:
- Add an option flag or reuse existing webhook_token presence to gate validation.
- Keep JSON ["ok"] responses and fast-ack behavior.
- Log invalid token attempts at warning level without leaking secrets.
Risks:
- Misconfigured tokens could block events if Omlet omits the header/body.
Tests:
- Webhook handler tests for: no token configured, valid token, invalid token, and non-JSON payload.
Status: Completed (2026-01-01)
Validation:
- Manual webhook tests confirmed delivery with token validation enabled.

2) Test suite for core submission readiness
Goal: Establish baseline tests required for HA core review.
Outline:
- Add config flow tests (valid/invalid API key, options flow save).
- Add coordinator update tests with mocked API responses and error handling.
- Add entity setup test to assert device info, unique_id, and platform wiring.
Risks:
- Over-mocking HA internals can make tests brittle.
Tests:
- Pytest with HA fixtures, minimal mocking of HA core helpers.

3) Metadata and registry audit
Goal: Ensure all entities/devices are HA-compliant and stable.
Outline:
- Verify unique_id stability across upgrades.
- Confirm device_info includes identifiers, manufacturer, model, sw_version.
- Mark entity_category for config/diagnostic entities consistently.
Risks:
- Changing unique_id could orphan entities.
Tests:
- Registry fixture tests to confirm unique_id and device_info consistency.
Status: Completed (2026-01-02)
Notes:
- Updated device_info identifiers to include deviceId alongside serial and removed hw_version placeholder.
Validation:
- Reviewed entity_category usage for config/diagnostic entities; no changes required.

4) Translation and UX alignment for core
Goal: Align strings/translations with core standards.
Outline:
- Move base strings to strings.json (core-style).
- Keep translations structure compatible with HA core pipeline.
- Audit user-facing strings for consistency and clarity.
Risks:
- Translation key changes can affect UI labels.
Tests:
- hassfest translation validation; manual UI spot-check.
Status: Completed (2026-01-02)
Notes:
- Moved English base strings to strings.json; kept translations/en.json in sync for HA 2025.12 runtime compatibility.

5) Core integration packaging prep
Goal: Prepare for upstreaming to home-assistant/core.
Outline:
- Remove manifest version for core.
- Ensure no custom-only files or HACS metadata are relied on.
- Draft documentation for home-assistant.io and align README accordingly.
Risks:
- Core submission will require additional code review changes.
Tests:
- hassfest and ruff; minimal integration tests in core layout.

6) Smart feeder device support
Goal: Add support for Omlet Smart No Waste Chicken Feeder devices (deviceType "Feeder").
Outline:
- Parse feeder state/config fields and surface them as entities.
- Add a feeder cover entity for open/close actions using the action endpoint list.
- Add feeder sensors for feed level, state, fault, light level, and last open/close timestamps.
- Update translations and README for new device type.
Risks:
- State values for the feeder may differ from the coop door (opening/closing semantics).
- Some actions (factory reset/firmware/setup wifi) are unsafe to expose directly.
Tests:
- Manual device setup with feeder JSON payload and open/close action.
Status: Implemented (2026-01-28)
Validation:
- Pending manual verification in HA.

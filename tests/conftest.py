"""Pytest configuration for Home Assistant custom component tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Resolve this repo's `custom_components` before Home Assistant's test harness
# (pytest-homeassistant-custom-component uses its own testing_config tree).
_ROOT = Path(__file__).resolve().parent.parent
_root_str = str(_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)
sys.modules.pop("custom_components", None)

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations) -> None:
    """Required by pytest-homeassistant-custom-component (see package README)."""

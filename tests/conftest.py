"""Test fixtures for the Brunner integration."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom_components/ in tests."""
    yield

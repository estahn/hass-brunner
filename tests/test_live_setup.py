"""Live setup test: real HA core + real touchdisplay.

Skipped unless BRUNNER_TEST_HOST is set (e.g. the display's IP), so CI and
offline runs skip it. It sets up a config entry exactly as the UI would, runs
the coordinator's first refresh against the hardware, and asserts the entities
populate with real values.
"""

import os

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brunner.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

HOST = os.environ.get("BRUNNER_TEST_HOST")


@pytest.mark.skipif(not HOST, reason="set BRUNNER_TEST_HOST to run the live test")
async def test_live_setup_populates_entities(
    hass: HomeAssistant, socket_enabled
) -> None:
    # The live test must reach the display on the LAN; lift pytest-socket's guard.
    import pytest_socket

    pytest_socket.enable_socket()
    if HOST:
        pytest_socket.socket_allow_hosts([HOST, "127.0.0.1", "::1"], allow_unix_socket=True)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: 5900, CONF_SCAN_INTERVAL: 300},
        unique_id=f"{HOST}:5900",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    states = {
        s.entity_id: s.state
        for s in hass.states.async_all()
        if s.entity_id.split(".", 1)[0] in ("sensor", "binary_sensor")
    }
    for eid in sorted(states):
        print(f"{eid} = {states[eid]}")

    assert len(states) >= 20, f"expected >=20 entities, got {len(states)}"
    populated = [v for v in states.values() if v not in ("unknown", "unavailable")]
    assert len(populated) >= 15, f"too few populated values: {states}"

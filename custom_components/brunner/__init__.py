"""The Brunner Heating integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import BrunnerCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

BrunnerConfigEntry = ConfigEntry[BrunnerCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BrunnerConfigEntry) -> bool:
    """Set up Brunner Heating from a config entry."""
    coordinator = BrunnerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BrunnerConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: BrunnerConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

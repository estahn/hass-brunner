"""Binary sensor platform for Brunner Heating."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BrunnerConfigEntry
from .const import DOMAIN
from .coordinator import BrunnerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrunnerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Brunner binary sensors."""
    async_add_entities(
        [
            BrunnerRunningSensor(entry.runtime_data, entry.entry_id),
            BrunnerStovePumpSensor(entry.runtime_data, entry.entry_id),
        ]
    )


class BrunnerRunningSensor(CoordinatorEntity[BrunnerCoordinator], BinarySensorEntity):
    """Whether the heat pump is actively running (derived from flow/heat)."""

    _attr_has_entity_name = True
    _attr_name = "Heat pump running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: BrunnerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_bwp_running"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Brunner Heating",
            manufacturer="Ulrich Brunner GmbH",
            model="BWP 13 green",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get("bwp_running")
        return value if isinstance(value, bool) else None


class BrunnerStovePumpSensor(
    CoordinatorEntity[BrunnerCoordinator], BinarySensorEntity
):
    """Whether the wood stove's charging pump is running (stove power > 0)."""

    _attr_has_entity_name = True
    _attr_name = "Stove pump"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: BrunnerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_stove_pump"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Brunner Heating",
            manufacturer="Ulrich Brunner GmbH",
            model="BWP 13 green",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get("stove_pump")
        return value if isinstance(value, bool) else None

"""Sensor platform for Brunner Heating.

Entity definitions mirror docs/sensor-map.md. The descriptions below are the
scaffold; the coordinator fills their values once per-screen OCR is implemented
in the poller build. Each key here must match a key produced by the coordinator.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BrunnerConfigEntry
from .const import DOMAIN
from .coordinator import BrunnerCoordinator


@dataclass(frozen=True, kw_only=True)
class BrunnerSensorDescription(SensorEntityDescription):
    """A sensor backed by a coordinator data key."""

    value_key: str


def _t(key: str, name: str) -> BrunnerSensorDescription:
    return BrunnerSensorDescription(
        key=key,
        value_key=key,
        name=name,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    )


# Mirrors docs/sensor-map.md. Extend as the poller gains screens.
SENSORS: tuple[BrunnerSensorDescription, ...] = (
    # Heat pump (BWP)
    _t("bwp_outdoor_temp", "Outdoor temperature"),
    _t("bwp_flow_temp", "Heat pump flow temperature"),
    _t("bwp_return_temp", "Heat pump return temperature"),
    _t("bwp_air_intake_temp", "Heat pump air intake temperature"),
    BrunnerSensorDescription(
        key="bwp_flow_rate", value_key="bwp_flow_rate",
        name="Heat pump flow rate",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrunnerSensorDescription(
        key="bwp_fan", value_key="bwp_fan", name="Heat pump fan",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrunnerSensorDescription(
        key="bwp_compressor_speed", value_key="bwp_compressor_speed",
        name="Heat pump compressor speed",
        native_unit_of_measurement="rev/s",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrunnerSensorDescription(
        key="bwp_heating_power", value_key="bwp_heating_power",
        name="Heat pump heating power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrunnerSensorDescription(
        key="bwp_cop", value_key="bwp_cop", name="Heat pump COP",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrunnerSensorDescription(
        key="bwp_pressure_high", value_key="bwp_pressure_high",
        name="Heat pump high pressure",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrunnerSensorDescription(
        key="bwp_pressure_low", value_key="bwp_pressure_low",
        name="Heat pump low pressure",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrunnerSensorDescription(
        key="bwp_status", value_key="bwp_status", name="Heat pump status",
    ),
    # Buffer / system overview
    _t("buffer_top_temp", "Buffer top temperature"),
    _t("buffer_middle_temp", "Buffer middle temperature"),
    _t("buffer_bottom_temp", "Buffer bottom temperature"),
    # Heating circuit 1
    _t("hk1_flow_set", "Heating circuit 1 flow setpoint"),
    _t("hk1_flow_actual", "Heating circuit 1 flow temperature"),
    _t("hk1_return_actual", "Heating circuit 1 return temperature"),
    BrunnerSensorDescription(
        key="hk1_flow_rate", value_key="hk1_flow_rate",
        name="Heating circuit 1 flow rate",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Hot water
    _t("dhw_set_temp", "Hot water setpoint"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrunnerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Brunner sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        BrunnerSensor(coordinator, entry.entry_id, desc) for desc in SENSORS
    )


class BrunnerSensor(CoordinatorEntity[BrunnerCoordinator], SensorEntity):
    """A single value read off the Brunner touchdisplay."""

    _attr_has_entity_name = True
    entity_description: BrunnerSensorDescription

    def __init__(
        self,
        coordinator: BrunnerCoordinator,
        entry_id: str,
        description: BrunnerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Brunner Heating",
            manufacturer="Ulrich Brunner GmbH",
            model="BWP 13 green",
        )

    @property
    def native_value(self) -> object:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.value_key)

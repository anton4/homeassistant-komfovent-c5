"""Sensor platform for Komfovent C5 integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_AIR_COOLER_HOURS,
    REG_AIR_HEATER_HOURS,
    REG_AIR_HEATER_KWH,
    REG_AIR_QUALITY_LEVEL,
    REG_ALARM_COUNT,
    REG_ALARM_DOUT,
    REG_CURRENT_EXHAUST_FLOW,
    REG_CURRENT_MODE,
    REG_CURRENT_SUPPLY_FLOW,
    REG_EFFICIENCY,
    REG_ELECTRIC_HEATER_LEVEL,
    REG_ENERGY_SAVING,
    REG_EXCHANGER_RECOVERY,
    REG_EXHAUST_FAN_HOURS,
    REG_EXHAUST_FAN_LEVEL,
    REG_EXHAUST_FAN_POWER,
    REG_EXHAUST_SFP,
    REG_EXHAUST_TEMP,
    REG_EXTRACT_FILTER_DIRTY,
    REG_EXTRACT_FILTER_IMPURITY,
    REG_EXTRACT_FLOW_SETPOINT,
    REG_EXTRACT_PRESSURE,
    REG_EXTRACT_TEMP,
    REG_HEAT_EXCHANGER_KWH,
    REG_HEAT_EXCHANGER_LEVEL,
    REG_INTERNAL_SUPPLY_TEMP,
    REG_OUTDOOR_FILTER_DIRTY,
    REG_OUTDOOR_FILTER_IMPURITY,
    REG_OUTDOOR_TEMP,
    REG_RETURN_WATER_TEMP,
    REG_STATUS,
    REG_SUPPLY_FAN_HOURS,
    REG_SUPPLY_FAN_LEVEL,
    REG_SUPPLY_FAN_POWER,
    REG_SUPPLY_FLOW_SETPOINT,
    REG_SUPPLY_HUMIDITY,
    REG_SUPPLY_PRESSURE,
    REG_SUPPLY_SFP,
    REG_SUPPLY_TEMP,
    REG_SUPPLY_TEMP_SETPOINT,
    REG_TEMP_SETPOINT,
    REG_WATER_COOLER_LEVEL,
    REG_WATER_HEATER_LEVEL,
)
from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

ALARM_MAP = {
    1: "Low supply air flow",
    2: "Low extract air flow",
    3: "VAV calibration fail",
    4: "Change outdoor air filter",
    5: "Change extract air filter",
    # ... Add remainder of your alarms here if missing!
}

@dataclass(frozen=True, kw_only=True)
class KomfoventSensorEntityDescription(SensorEntityDescription):
    """Class describing Komfovent sensor entities."""
    value_fn: Callable[[Any], StateType] | None = None

SENSORS: tuple[KomfoventSensorEntityDescription, ...] = (
    KomfoventSensorEntityDescription(
        key="rtc_time",
        name="Controller Clock Time",
        icon="mdi:clock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Operations
    KomfoventSensorEntityDescription(
        key=REG_STATUS,
        name="Operation Status",
        value_fn=lambda val: {
            0: "Stopped",
            1: "Idle (Fans Stopped)",
            2: "Running",
        }.get(val, f"Unknown ({val})"),
    ),
    KomfoventSensorEntityDescription(
        key=REG_CURRENT_MODE,
        name="Current Mode",
        value_fn=lambda val: {
            0: "Standby",
            1: "Comfort 1",
            2: "Comfort 2",
            3: "Economy 1",
            4: "Economy 2",
            5: "Special",
            6: "Program",
        }.get(val, f"Unknown ({val})"),
    ),
    # Temperatures
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_TEMP,
        name="Supply Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXTRACT_TEMP,
        name="Extract Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_OUTDOOR_TEMP,
        name="Outdoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXHAUST_TEMP,
        name="Exhaust Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_RETURN_WATER_TEMP,
        name="Return Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_INTERNAL_SUPPLY_TEMP,
        name="Internal Supply Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Flow
    KomfoventSensorEntityDescription(
        key=REG_CURRENT_SUPPLY_FLOW,
        name="Current Supply Flow",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_CURRENT_EXHAUST_FLOW,
        name="Current Exhaust Flow",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_FLOW_SETPOINT,
        name="Supply Flow Setpoint",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXTRACT_FLOW_SETPOINT,
        name="Extract Flow Setpoint",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Pressures
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_PRESSURE,
        name="Supply Air Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXTRACT_PRESSURE,
        name="Extract Air Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Fan level & Power
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_FAN_LEVEL,
        name="Supply Fan Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXHAUST_FAN_LEVEL,
        name="Exhaust Fan Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_FAN_POWER,
        name="Current Supply Fan Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXHAUST_FAN_POWER,
        name="Current Exhaust Fan Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Exchanger Levels
    KomfoventSensorEntityDescription(
        key=REG_HEAT_EXCHANGER_LEVEL,
        name="Heat Exchanger Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_ELECTRIC_HEATER_LEVEL,
        name="Electric Heater Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_WATER_HEATER_LEVEL,
        name="Water Heater Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_WATER_COOLER_LEVEL,
        name="Water Cooler Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Efficiency & recovery
    KomfoventSensorEntityDescription(
        key=REG_EFFICIENCY,
        name="Heat Exchanger Thermal Efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_ENERGY_SAVING,
        name="Energy Saving Efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXCHANGER_RECOVERY,
        name="Heat Exchanger Recovery Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Lifetime Counters (Hours)
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_FAN_HOURS,
        name="Supply Fan Operation",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXHAUST_FAN_HOURS,
        name="Exhaust Fan Operation",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KomfoventSensorEntityDescription(
        key=REG_AIR_HEATER_HOURS,
        name="Air Heater Operation Hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KomfoventSensorEntityDescription(
        key=REG_AIR_COOLER_HOURS,
        name="Air Cooler Operation Hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Lifetime Energy (kWh)
    KomfoventSensorEntityDescription(
        key=REG_HEAT_EXCHANGER_KWH,
        name="Heat Exchanger Energy Recovered",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    KomfoventSensorEntityDescription(
        key=REG_AIR_HEATER_KWH,
        name="Air Heater Energy Consumed",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # Specific Fan Power (SFP)
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_SFP,
        name="Supply Specific Fan Power",
        native_unit_of_measurement="kW/(m³/s)",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXHAUST_SFP,
        name="Exhaust Specific Fan Power",
        native_unit_of_measurement="kW/(m³/s)",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Filters
    KomfoventSensorEntityDescription(
        key=REG_OUTDOOR_FILTER_IMPURITY,
        name="Outdoor Filter Impurity Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXTRACT_FILTER_IMPURITY,
        name="Extract Filter Impurity Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_OUTDOOR_FILTER_DIRTY,
        name="Outdoor Filter Status",
        value_fn=lambda val: "Dirty" if val == 1 else "Clean",
    ),
    KomfoventSensorEntityDescription(
        key=REG_EXTRACT_FILTER_DIRTY,
        name="Extract Filter Status",
        value_fn=lambda val: "Dirty" if val == 1 else "Clean",
    ),
    # Humidity & AQ
    KomfoventSensorEntityDescription(
        key=REG_SUPPLY_HUMIDITY,
        name="Supply Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_AIR_QUALITY_LEVEL,
        name="Air Quality Level",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Alarms
    KomfoventSensorEntityDescription(
        key=REG_ALARM_COUNT,
        name="Active Alarms Count",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KomfoventSensorEntityDescription(
        key=REG_ALARM_DOUT,
        name="Alarm DOUT",
        value_fn=lambda val: "Active Alarms" if val == 1 else "No Alarms",
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent C5 sensors."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        KomfoventSensor(coordinator, description)
        for description in SENSORS
    ]
    
    # Also add the custom alarm list text sensor
    entities.append(KomfoventAlarmSensor(coordinator))
    
    async_add_entities(entities)

class KomfoventSensor(CoordinatorEntity[KomfoventCoordinator], SensorEntity):
    """Representation of a Komfovent sensor."""

    entity_description: KomfoventSensorEntityDescription

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        description: KomfoventSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        
        self._attr_name = f"{coordinator.name} {description.name}"
        self._attr_unique_id = f"{coordinator.host}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        raw_val = self.coordinator.data.get(self.entity_description.key)
        if raw_val is None:
            return None
            
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(raw_val)
            
        return raw_val

class KomfoventAlarmSensor(CoordinatorEntity[KomfoventCoordinator], SensorEntity):
    """Sensor that represents list of active alarms in a readable text format."""

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the alarm sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.name} Active Alarms List"
        self._attr_unique_id = f"{coordinator.host}_active_alarms_list"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    @property
    def native_value(self) -> str:
        """Return the active alarms as a comma-separated list of names."""
        alarm_codes = self.coordinator.data.get("alarm_codes")
        if not alarm_codes:
            return "No Alarms"
            
        descriptions = [
            ALARM_MAP.get(code, f"Unknown Alarm Code {code}")
            for code in alarm_codes
        ]
        return ", ".join(descriptions)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return raw alarm codes as attributes."""
        return {
            "alarm_codes": self.coordinator.data.get("alarm_codes", [])
        }

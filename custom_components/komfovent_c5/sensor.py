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
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_AIR_QUALITY_LEVEL,
    REG_ALARM_COUNT,
    REG_ALARM_DOUT,
    REG_CURRENT_EXHAUST_FLOW,
    REG_CURRENT_MODE,
    REG_CURRENT_SUPPLY_FLOW,
    REG_EFFICIENCY,
    REG_ENERGY_SAVING,
    REG_EXCHANGER_RECOVERY,
    REG_EXHAUST_FAN_LEVEL,
    REG_EXHAUST_SFP,
    REG_EXHAUST_TEMP,
    REG_EXTRACT_FILTER_DIRTY,
    REG_EXTRACT_FILTER_IMPURITY,
    REG_EXTRACT_FLOW_SETPOINT,
    REG_EXTRACT_PRESSURE,
    REG_EXTRACT_TEMP,
    REG_INTERNAL_SUPPLY_TEMP,
    REG_OUTDOOR_FILTER_DIRTY,
    REG_OUTDOOR_FILTER_IMPURITY,
    REG_OUTDOOR_TEMP,
    REG_RETURN_WATER_TEMP,
    REG_STATUS,
    REG_SUPPLY_FAN_LEVEL,
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
    12: "High pressure on compressor",
    13: "Low pressure on compressor",
    14: "Service time",
    15: "Evaporator icing",
    16: "Heat pump malfunction",
    17: "Heat pump malfunction",
    18: "Heat pump malfunction",
    19: "Compressor off",
    20: "Compressor off",
    21: "High pressure on compressor",
    22: "Low pressure on compressor",
    44: "Heat pump malfunction or Communication error",
    59: "Heat pump malfunction or Communication error",
    83: "Heat pump malfunction or Communication error",
    95: "Low heat exchanger efficiency",
    97: "Communication error",
    99: "Communication error",
    112: "Water pump/coil alarm",
    113: "CF or HP exchanger not calibrated",
    114: "CF or HP exchanger not calibrated",
    115: "High pressure on compressor",
    116: "Low pressure on compressor",
    126: "Unknown alarm",
    127: "Service mode",
    128: "Supply air temp. Sensor failure",
    129: "Supply air temp. Sensor failure",
    130: "Extract air temp. Sensor failure",
    131: "Extract air temp. Sensor failure",
    132: "Outdoor air temp. Sensor failure",
    133: "Outdoor air temp. Sensor failure",
    134: "Exhaust air temp. Sensor failure",
    135: "Exhaust air temp. Sensor failure",
    136: "Water temp. sensor failure",
    137: "Water temp. sensor failure",
    138: "Return water temp. low",
    139: "Internal fire alarm",
    140: "External fire alarm",
    141: "External stop",
    142: "Heat exchanger failure",
    143: "Heat exchanger icing",
    144: "Low supply air temperature",
    145: "High supply air temperature",
    146: "Low supply air flow",
    147: "Low extract air flow",
    149: "Electric heater overheat",
    152: "Evaporator air temp. Sensor failure",
    153: "Evaporator coil temp. Sensor failure",
    156: "Compressor failure",
    170: "External stop",
    172: "Water pump/coil alarm",
    173: "CF exchanger not calibrated",
    210: "Controller failure",
    211: "Communication error",
    217: "Service mode",
    226: "Supply fan drive failure",
    227: "Supply fan drive overload",
    228: "Supply fan motor failure",
    230: "Supply fan motor overload",
    231: "Exhaust fan drive failure",
    232: "Exhaust fan drive oveload",
    233: "Exhaust fan motor failure",
    234: "Exhaust fan motor overload",
    236: "Rotor drive failure",
    237: "Rotor drive overload",
    238: "Rotor motor failure",
    239: "Rotor motor overload",
}

@dataclass(frozen=True, kw_only=True)
class KomfoventSensorEntityDescription(SensorEntityDescription):
    """Class describing Komfovent sensor entities."""
    value_fn: Callable[[Any], StateType] | None = None

SENSORS: tuple[KomfoventSensorEntityDescription, ...] = (
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
    # Fan level
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
    # Exchanger Levels
    KomfoventSensorEntityDescription(
        key=REG_HEAT_EXCHANGER_LEVEL,
        name="Heat Exchanger Level",
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
        self._attr_unique_id = f"{coordinator.client.params.host}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.params.host)},
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
        self._attr_unique_id = f"{coordinator.client.params.host}_active_alarms_list"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.params.host)},
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

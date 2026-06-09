"""Switch platform for Komfovent C5 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_SPECIAL_CONFIGURATION,
    REG_DEMAND_CONTROL,
    REG_OVERRIDE_ENABLE,
    REG_RECIRC_CONTROL,
    REG_SUMMER_COOLING,
)
from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

# Map the bits for Special Mode
SPECIAL_CONFIG_BITS = {
    0: ("Special Mode: Heating Enable", "mdi:radiator"),
    1: ("Special Mode: Cooling Enable", "mdi:snowflake"),
    2: ("Special Mode: Recirculation Enable", "mdi:sync"),
    3: ("Special Mode: Humidifying Enable", "mdi:water-percent"),
    4: ("Special Mode: Dehumidifying Enable", "mdi:water-off"),
}

# Map the registers for Standard Features
STANDARD_SWITCHES = {
    REG_DEMAND_CONTROL: ("Operation on Demand", "mdi:leaf"),
    REG_OVERRIDE_ENABLE: ("Override Function", "mdi:clock-fast"),
    REG_RECIRC_CONTROL: ("Recirculation Control", "mdi:sync-circle"),
    REG_SUMMER_COOLING: ("Summer Night Cooling", "mdi:weather-night"),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent C5 switch entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Load Special Config Switches
    for bit, (name, icon) in SPECIAL_CONFIG_BITS.items():
        entities.append(KomfoventSpecialConfigSwitch(coordinator, bit, name, icon))
        
    # Load Standard Switches
    for reg, (name, icon) in STANDARD_SWITCHES.items():
        entities.append(KomfoventStandardSwitch(coordinator, reg, name, icon))
    
    async_add_entities(entities)

class KomfoventSpecialConfigSwitch(CoordinatorEntity[KomfoventCoordinator], SwitchEntity):
    """Switch to control a specific feature bit in Special Mode."""

    def __init__(self, coordinator: KomfoventCoordinator, bit: int, name: str, icon: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.bit = bit
        self._attr_name = f"{coordinator.name} {name}"
        self._attr_unique_id = f"{coordinator.host}_special_config_bit_{bit}"
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the bit is set to 1."""
        val = self.coordinator.data.get(REG_SPECIAL_CONFIGURATION)
        if val is None:
            return None
        return bool(val & (1 << self.bit))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set the bit to 1."""
        await self.coordinator.async_set_special_config_bit(self.bit, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Set the bit to 0."""
        await self.coordinator.async_set_special_config_bit(self.bit, False)

class KomfoventStandardSwitch(CoordinatorEntity[KomfoventCoordinator], SwitchEntity):
    """Switch to control standard C5 boolean features."""

    def __init__(self, coordinator: KomfoventCoordinator, reg: int, name: str, icon: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.reg = reg
        self._attr_name = f"{coordinator.name} {name}"
        self._attr_unique_id = f"{coordinator.host}_std_switch_{reg}"
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the register is 1."""
        val = self.coordinator.data.get(self.reg)
        if val is None:
            return None
        return val == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set the register to 1."""
        await self.coordinator.async_write_register(self.reg, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Set the register to 0."""
        await self.coordinator.async_write_register(self.reg, 0)

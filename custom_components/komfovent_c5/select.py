"""Select platform for Komfovent C5 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_TEMP_CONTROL_MODE
from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

# Map the Modbus integers to human-readable dropdown options
OPTIONS_MAP = {
    0: "Supply Air",
    1: "Extract Air",
    2: "Room Control",
}
# Create a reverse map to translate the dropdown text back into an integer for Modbus
REVERSE_MAP = {v: k for k, v in OPTIONS_MAP.items()}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent C5 select entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        KomfoventTempControlSelect(coordinator)
    ])

class KomfoventTempControlSelect(CoordinatorEntity[KomfoventCoordinator], SelectEntity):
    """Dropdown menu for Temperature Control Mode."""

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        
        self._attr_name = f"{coordinator.name} Temperature Control Mode"
        self._attr_unique_id = f"{coordinator.host}_temp_control_mode"
        self._attr_icon = "mdi:home-thermometer"
        self._attr_options = list(OPTIONS_MAP.values())
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected option from the controller."""
        val = self.coordinator.data.get(REG_TEMP_CONTROL_MODE)
        return OPTIONS_MAP.get(val)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option and write it to Modbus."""
        val = REVERSE_MAP.get(option)
        if val is not None:
            await self.coordinator.async_write_register(REG_TEMP_CONTROL_MODE, val)

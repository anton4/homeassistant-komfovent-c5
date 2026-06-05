"""Number platform for Komfovent C5 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_SPECIAL_EXTRACT_FLOW, REG_SPECIAL_SUPPLY_FLOW
from .coordinator import KomfoventCoordinator, encode_32bit

_LOGGER = logging.getLogger(__name__)

NUMBERS: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key=REG_SPECIAL_SUPPLY_FLOW,
        name="Special Mode Supply Flow",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:fan-chevron-up",
    ),
    NumberEntityDescription(
        key=REG_SPECIAL_EXTRACT_FLOW,
        name="Special Mode Extract Flow",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:fan-chevron-down",
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent C5 number entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        [KomfoventNumber(coordinator, description) for description in NUMBERS]
    )

class KomfoventNumber(CoordinatorEntity[KomfoventCoordinator], NumberEntity):
    """Representation of a Komfovent Flow percentage."""

    entity_description: NumberEntityDescription

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
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
        
        # 0% completely turns off the fan, otherwise it must be 20%-100%
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        val = self.coordinator.data.get(self.entity_description.key)
        if val is None:
            return None
        return float(val)

    async def async_set_native_value(self, value: float) -> None:
        """Update the flow value."""
        int_value = int(value)
        # Flow is a 32-bit register, so we encode it to a list of two 16-bit integers
        encoded_values = encode_32bit(int_value)
        await self.coordinator.async_write_registers(self.entity_description.key, encoded_values)

"""Switch platform for Komfovent C5 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_DEMAND_CONTROL,
    REG_ELECTRIC_HEATER,
    REG_OVERRIDE_ENABLE,
    REG_RECIRC_CONTROL,
    REG_SUMMER_COOLING,
    REG_WATER_COOLER,
    REG_WATER_HEATER,
)
from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

SWITCHES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key=REG_OVERRIDE_ENABLE,
        name="Override Function",
        icon="mdi:clock-fast",
    ),
    SwitchEntityDescription(
        key=REG_SUMMER_COOLING,
        name="Summer Night Cooling",
        icon="mdi:weather-night",
    ),
    SwitchEntityDescription(
        key=REG_DEMAND_CONTROL,
        name="Operation on Demand",
        icon="mdi:leaf",
    ),
    SwitchEntityDescription(
        key=REG_RECIRC_CONTROL,
        name="Recirculation Control",
        icon="mdi:cached",
    ),
    SwitchEntityDescription(
        key=REG_WATER_HEATER,
        name="Water Heater Enable",
        icon="mdi:water-heating",
    ),
    SwitchEntityDescription(
        key=REG_WATER_COOLER,
        name="Water Cooler Enable",
        icon="mdi:snowflake",
    ),
    SwitchEntityDescription(
        key=REG_ELECTRIC_HEATER,
        name="Electric Heater Enable",
        icon="mdi:radiator",
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent C5 switches."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        [KomfoventSwitch(coordinator, description) for description in SWITCHES]
    )

class KomfoventSwitch(CoordinatorEntity[KomfoventCoordinator], SwitchEntity):
    """Representation of a Komfovent switch."""

    entity_description: SwitchEntityDescription

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
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
    def is_on(self) -> bool | None:
        """Return True if switch is on."""
        val = self.coordinator.data.get(self.entity_description.key)
        if val is None:
            return None
        return val == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.async_write_register(self.entity_description.key, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.async_write_register(self.entity_description.key, 0)

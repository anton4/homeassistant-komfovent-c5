"""Climate platform for Komfovent C5 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MODE_TO_SETPOINT_REG,
    PRESET_COMFORT1,
    PRESET_COMFORT2,
    PRESET_ECONOMY1,
    PRESET_ECONOMY2,
    PRESET_PROGRAM,
    PRESET_SPECIAL,
    PRESET_STANDBY,
    PRESET_TO_REG,
    REG_COMFORT1_TEMP,
    REG_CURRENT_MODE,
    REG_EXTRACT_TEMP,
    REG_ON_OFF,
    REG_STATUS,
    REG_TEMP_SETPOINT,
    REG_TO_PRESET,
)
from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Komfovent C5 climate entity."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KomfoventClimate(coordinator)])

class KomfoventClimate(CoordinatorEntity[KomfoventCoordinator], ClimateEntity):
    """Representation of Komfovent C5 Climate control."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [
        PRESET_COMFORT1,
        PRESET_COMFORT2,
        PRESET_ECONOMY1,
        PRESET_ECONOMY2,
        PRESET_SPECIAL,
        PRESET_PROGRAM,
    ]
    _attr_min_temp = 5.0
    _attr_max_temp = 40.0
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_name = coordinator.name
        self._attr_unique_id = f"{coordinator.client.params.host}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.params.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        on_off = self.coordinator.data.get(REG_ON_OFF)
        if on_off == 0:
            return HVACMode.OFF
        return HVACMode.FAN_ONLY

    @property
    def current_temperature(self) -> float | None:
        """Return current extract temperature (representing room air)."""
        return self.coordinator.data.get(REG_EXTRACT_TEMP)

    @property
    def target_temperature(self) -> float | None:
        """Return current target temperature setpoint."""
        return self.coordinator.data.get(REG_TEMP_SETPOINT)

    @property
    def preset_mode(self) -> str | None:
        """Return current active preset mode."""
        current_mode = self.coordinator.data.get(REG_CURRENT_MODE)
        if current_mode is None:
            return None
        return REG_TO_PRESET.get(current_mode)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write_register(REG_ON_OFF, 0)
        else:
            await self.coordinator.async_write_register(REG_ON_OFF, 1)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        if preset_mode not in PRESET_TO_REG:
            _LOGGER.error("Invalid preset mode: %s", preset_mode)
            return
        
        reg_value = PRESET_TO_REG[preset_mode]
        await self.coordinator.async_write_register(100, reg_value)

    async def async_set_target_temperature(self, **kwargs: Any) -> None:
        """Set target temperature (write to active mode setpoint register)."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        current_mode = self.coordinator.data.get(REG_CURRENT_MODE)
        if current_mode is None:
            current_mode = 1  # Fallback to Comfort 1
            
        # Determine setpoint register corresponding to the current running mode
        setpoint_reg = MODE_TO_SETPOINT_REG.get(current_mode, REG_COMFORT1_TEMP)
        
        # C5 scale is x10 (e.g. 21.5°C -> 215)
        reg_val = int(temperature * 10)
        await self.coordinator.async_write_register(setpoint_reg, reg_val)

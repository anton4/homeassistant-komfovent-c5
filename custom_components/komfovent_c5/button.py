"""Button platform for Komfovent C5 integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent C5 button entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        KomfoventSyncTimeButton(coordinator),
        KomfoventResetAlarmsButton(coordinator),
        KomfoventCalibrateFiltersButton(coordinator),
        KomfoventResetCountersButton(coordinator),
        KomfoventResetServiceTimerButton(coordinator)
    ])

class KomfoventSyncTimeButton(CoordinatorEntity[KomfoventCoordinator], ButtonEntity):
    """Button to sync the C5 clock with Home Assistant."""

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        
        self._attr_name = f"{coordinator.name} Sync Clock to HA"
        self._attr_unique_id = f"{coordinator.host}_sync_clock"
        self._attr_icon = "mdi:update"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_sync_time()

class KomfoventResetAlarmsButton(CoordinatorEntity[KomfoventCoordinator], ButtonEntity):
    """Button to reset alarms on the C5 controller."""

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        
        self._attr_name = f"{coordinator.name} Reset Alarms"
        self._attr_unique_id = f"{coordinator.host}_reset_alarms"
        self._attr_icon = "mdi:shield-refresh"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_reset_alarms()

class KomfoventCalibrateFiltersButton(CoordinatorEntity[KomfoventCoordinator], ButtonEntity):
    """Button to calibrate clean air filters."""

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        
        self._attr_name = f"{coordinator.name} Calibrate Clean Filters"
        self._attr_unique_id = f"{coordinator.host}_calibrate_filters"
        self._attr_icon = "mdi:air-filter"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_calibrate_filters()

class KomfoventResetCountersButton(CoordinatorEntity[KomfoventCoordinator], ButtonEntity):
    """Button to reset operation counters."""

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.name} Reset Operation Counters"
        self._attr_unique_id = f"{coordinator.host}_reset_counters"
        self._attr_icon = "mdi:counter"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_reset_operation_counters()

class KomfoventResetServiceTimerButton(CoordinatorEntity[KomfoventCoordinator], ButtonEntity):
    """Button to reset the service time counter."""

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.name} Reset Service Timer"
        self._attr_unique_id = f"{coordinator.host}_reset_service_timer"
        self._attr_icon = "mdi:wrench-clock"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": coordinator.name,
            "manufacturer": "Komfovent",
            "model": "C5 Controller",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_reset_service_timer()

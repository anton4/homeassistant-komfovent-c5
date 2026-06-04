"""The Komfovent C5 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import CONF_SLAVE_ID, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Komfovent C5 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    slave_id = entry.data[CONF_SLAVE_ID]
    scan_interval = DEFAULT_SCAN_INTERVAL

    _LOGGER.debug(
        "Setting up Komfovent C5 integration for %s on port %s with slave ID %s",
        host,
        port,
        slave_id,
    )

    coordinator = KomfoventCoordinator(
        hass,
        host=host,
        port=port,
        slave_id=slave_id,
        scan_interval=scan_interval,
    )

    # Perform first refresh to verify communication works before completing setup
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Close Modbus connection
    coordinator.client.close()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

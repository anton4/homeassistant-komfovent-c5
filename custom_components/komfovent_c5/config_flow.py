"""Config flow for Komfovent C5 integration."""
from __future__ import annotations

import inspect
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import CONF_SLAVE_ID, DEFAULT_NAME, DEFAULT_PORT, DOMAIN, REG_STATUS

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    slave_id = data[CONF_SLAVE_ID]

    _LOGGER.debug("Validating connection to %s:%s with slave ID %s", host, port, slave_id)
    client = AsyncModbusTcpClient(host=host, port=port, timeout=5.0)
    
    try:
        connected = await client.connect()
        if not connected:
            _LOGGER.error("Failed to connect to Modbus TCP client on %s:%s", host, port)
            raise CannotConnect

        # 0-Indexed test read
        wire_address = REG_STATUS - 1
        
        sig = inspect.signature(client.read_holding_registers)
        kwargs = {}
        if 'device_id' in sig.parameters: kwargs['device_id'] = slave_id
        elif 'slave' in sig.parameters: kwargs['slave'] = slave_id
        elif 'unit' in sig.parameters: kwargs['unit'] = slave_id
        else: kwargs['slave'] = slave_id

        if 'count' in sig.parameters or 'kwargs' in sig.parameters:
            kwargs['count'] = 1

        result = client.read_holding_registers(wire_address, **kwargs)
        if inspect.isawaitable(result):
            result = await result

        if result.isError():
            _LOGGER.error("Modbus read returned an error response: %s", result)
            raise CannotConnect
            
    except Exception as err:
        _LOGGER.exception("Error validating Modbus connection: %s", err)
        raise CannotConnect from err
    finally:
        client.close()

    # Safely get CONF_NAME, defaulting to DEFAULT_NAME for the options flow where Name isn't passed
    return {"title": data.get(CONF_NAME, DEFAULT_NAME)}


class KomfoventConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Komfovent C5."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return KomfoventOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception in config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                    vol.Optional(CONF_SLAVE_ID, default=1): cv.positive_int,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )


class KomfoventOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow for Komfovent C5 (Reconfiguration)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the Komfovent connection options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Test the new connection details
                await validate_input(self.hass, user_input)
                
                # Update the original entry.data with the new settings
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data={**self.config_entry.data, **user_input}
                )
                
                # Close the options flow modal
                return self.async_create_entry(title="", data={})
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception in options flow")
                errors["base"] = "unknown"

        # Pre-fill the form with the current settings from entry.data
        current_host = self.config_entry.data.get(CONF_HOST)
        current_port = self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
        current_slave_id = self.config_entry.data.get(CONF_SLAVE_ID, 1)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=current_host): str,
                    vol.Optional(CONF_PORT, default=current_port): cv.port,
                    vol.Optional(CONF_SLAVE_ID, default=current_slave_id): cv.positive_int,
                }
            ),
            errors=errors,
        )

class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

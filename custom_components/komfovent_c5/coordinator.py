"""Data update coordinator for Komfovent C5 integration."""
from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import timedelta
from typing import Any

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SLAVE_ID,
    DOMAIN,
    REG_AIR_QUALITY_LEVEL,
    REG_AIR_QUALITY_TYPE,
    REG_ALARM_COUNT,
    REG_ALARM_DOUT,
    REG_ALARM_START,
    REG_COMFORT1_TEMP,
    REG_COMFORT2_TEMP,
    REG_CURRENT_EXHAUST_FLOW,
    REG_CURRENT_MODE,
    REG_CURRENT_SUPPLY_FLOW,
    REG_DEMAND_CONTROL,
    REG_ECONOMY1_TEMP,
    REG_ECONOMY2_TEMP,
    REG_EFFICIENCY,
    REG_ELECTRIC_HEATER,
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
    REG_FLOW_CONTROL_MODE,
    REG_HEAT_EXCHANGER_LEVEL,
    REG_HUMIDITY_CONTROL_LEVEL,
    REG_INTERNAL_SUPPLY_TEMP,
    REG_ON_OFF,
    REG_OUTDOOR_FILTER_DIRTY,
    REG_OUTDOOR_FILTER_IMPURITY,
    REG_OUTDOOR_TEMP,
    REG_OVERRIDE_ENABLE,
    REG_OVERRIDE_MODE,
    REG_OVERRIDE_TYPE,
    REG_RECIRC_CONTROL,
    REG_RECIRCULATION_LEVEL,
    REG_RETURN_WATER_TEMP,
    REG_SPECIAL_TEMP,
    REG_STATUS,
    REG_SUMMER_COOLING,
    REG_SUPPLY_FAN_LEVEL,
    REG_SUPPLY_FLOW_SETPOINT,
    REG_SUPPLY_HUMIDITY,
    REG_SUPPLY_PRESSURE,
    REG_SUPPLY_SFP,
    REG_SUPPLY_TEMP,
    REG_SUPPLY_TEMP_SETPOINT,
    REG_TEMP_CONTROL_MODE,
    REG_TEMP_SETPOINT,
    REG_WATER_COOLER,
    REG_WATER_COOLER_LEVEL,
    REG_WATER_HEATER,
    REG_WATER_HEATER_LEVEL,
)

_LOGGER = logging.getLogger(__name__)

def to_signed_16(val: int) -> int:
    """Convert unsigned 16-bit int to signed 16-bit int."""
    if val >= 0x8000:
        return val - 0x10000
    return val

def decode_32bit(reg_high: int, reg_low: int) -> int:
    """Decode two 16-bit registers into a 32-bit integer (big-endian word order)."""
    return (reg_high << 16) + reg_low

class KomfoventCoordinator(DataUpdateCoordinator[dict[int | str, Any]]):
    """Class to manage fetching data from Komfovent C5 unit via Modbus."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        slave_id: int,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.client = AsyncModbusTcpClient(host=host, port=port)
        self.slave_id = slave_id
        
        # Add these two lines to save the connection details safely
        self.host = host
        self.port = port
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[int | str, Any]:
        """Fetch data from Modbus."""
        if not self.client.connected:
            _LOGGER.debug("Connecting to Modbus TCP server %s:%s", self.host, self.port)
            try:
                connected = await self.client.connect()
                if not connected:
                    raise UpdateFailed("Failed to establish Modbus TCP connection")
            except Exception as err:
                raise UpdateFailed(f"Modbus connection error: {err}") from err

        raw_data: dict[int | str, Any] = {}

        # Helper method to read registers handling pymodbus versions and 0-indexing
        async def _read_block(address: int, count: int) -> list[int] | None:
            wire_address = address - 1  # 0-indexing translation
            try:
                sig = inspect.signature(self.client.read_holding_registers)
                kwargs = {}
                
                if 'device_id' in sig.parameters: kwargs['device_id'] = self.slave_id
                elif 'slave' in sig.parameters: kwargs['slave'] = self.slave_id
                elif 'unit' in sig.parameters: kwargs['unit'] = self.slave_id
                else: kwargs['slave'] = self.slave_id

                if 'count' in sig.parameters or 'kwargs' in sig.parameters:
                    kwargs['count'] = count

                result = self.client.read_holding_registers(wire_address, **kwargs)
                if inspect.isawaitable(result):
                    result = await result
                
                if result.isError():
                    # We expect some blocks (like missing heaters) to return errors, log as debug to avoid spam
                    _LOGGER.debug("Modbus read returned error at address %s: %s", address, result)
                    return None
                return result.registers
            except Exception as err:
                _LOGGER.debug("Exception reading Modbus block starting at %s: %s", address, err)
                return None

        # Polling register blocks with 300ms delays to respect controller limits
        block_on_off = await _read_block(REG_ON_OFF, 1)
        await asyncio.sleep(0.3)
        block_modes = await _read_block(100, 29)
        await asyncio.sleep(0.3)
        block_override = await _read_block(REG_OVERRIDE_ENABLE, 9)
        await asyncio.sleep(0.3)
        
        # Split Heaters
        heater_water = await _read_block(REG_WATER_HEATER, 1)
        await asyncio.sleep(0.3)
        heater_cooler = await _read_block(REG_WATER_COOLER, 1)
        await asyncio.sleep(0.3)
        heater_electric = await _read_block(REG_ELECTRIC_HEATER, 1)
        await asyncio.sleep(0.3)
        
        block_alarms = await _read_block(REG_ALARM_COUNT, 11)
        await asyncio.sleep(0.3)
        
        # Split Monitoring (Block 6) into safe chunks
        block_mon_1 = await _read_block(2000, 24)       # 2000-2023
        await asyncio.sleep(0.3)
        block_mon_2 = await _read_block(2032, 2)        # 2032-2033
        await asyncio.sleep(0.3)
        block_mon_flow_sp = await _read_block(2036, 4)  # 2036-2039
        await asyncio.sleep(0.3)
        block_mon_3 = await _read_block(2040, 1)        # 2040
        await asyncio.sleep(0.3)
        block_mon_4 = await _read_block(2045, 1)        # 2045
        await asyncio.sleep(0.3)
        
        block_efficiency = await _read_block(REG_EFFICIENCY, 8)
        await asyncio.sleep(0.3)
        
        # Split Filters
        filter_outdoor = await _read_block(REG_OUTDOOR_FILTER_DIRTY, 1)
        await asyncio.sleep(0.3)
        filter_extract = await _read_block(REG_EXTRACT_FILTER_DIRTY, 1)

        # Validate critical blocks
        if block_on_off is None or block_mon_1 is None:
            _LOGGER.error("Could not read critical Modbus registers from Komfovent C5")
            self.client.close()
            raise UpdateFailed("Critical Modbus data blocks could not be read")

        # Parse Block 1 (On/Off)
        raw_data[REG_ON_OFF] = block_on_off[0]

        # Parse Block 2 (Modes/Setpoints)
        if block_modes:
            raw_data[100] = block_modes[0]  # REG_MODE_SELECT
            raw_data[REG_COMFORT1_TEMP] = block_modes[5]
            raw_data[REG_COMFORT2_TEMP] = block_modes[10]
            raw_data[REG_ECONOMY1_TEMP] = block_modes[15]
            raw_data[REG_ECONOMY2_TEMP] = block_modes[20]
            raw_data[REG_SPECIAL_TEMP] = block_modes[25]
            raw_data[REG_FLOW_CONTROL_MODE] = block_modes[27]
            raw_data[REG_TEMP_CONTROL_MODE] = block_modes[28]

        # Parse Block 3 (Override & Settings)
        if block_override:
            raw_data[REG_OVERRIDE_ENABLE] = block_override[0]
            raw_data[REG_OVERRIDE_TYPE] = block_override[1]
            raw_data[REG_OVERRIDE_MODE] = block_override[2]
            raw_data[REG_SUMMER_COOLING] = block_override[3]
            raw_data[REG_DEMAND_CONTROL] = block_override[5]
            raw_data[REG_RECIRC_CONTROL] = block_override[7]

        # Parse Block 4 (Heaters & Coolers) safely
        if heater_water: raw_data[REG_WATER_HEATER] = heater_water[0]
        if heater_cooler: raw_data[REG_WATER_COOLER] = heater_cooler[0]
        if heater_electric: raw_data[REG_ELECTRIC_HEATER] = heater_electric[0]

        # Parse Block 5 (Alarms)
        if block_alarms:
            raw_data[REG_ALARM_COUNT] = block_alarms[0]
            raw_data["alarm_codes"] = [code for code in block_alarms[1:] if code != 0]

        # Parse Block 6 (Monitoring Data Chunks)
        if block_mon_1:
            raw_data[REG_STATUS] = block_mon_1[0]
            raw_data[REG_CURRENT_MODE] = block_mon_1[1]
            raw_data[REG_CURRENT_SUPPLY_FLOW] = decode_32bit(block_mon_1[2], block_mon_1[3])
            raw_data[REG_CURRENT_EXHAUST_FLOW] = decode_32bit(block_mon_1[4], block_mon_1[5])
            raw_data[REG_SUPPLY_TEMP] = to_signed_16(block_mon_1[6]) / 10.0
            raw_data[REG_EXTRACT_TEMP] = to_signed_16(block_mon_1[7]) / 10.0
            raw_data[REG_OUTDOOR_TEMP] = to_signed_16(block_mon_1[8]) / 10.0
            raw_data[REG_EXHAUST_TEMP] = to_signed_16(block_mon_1[9]) / 10.0
            raw_data[REG_RETURN_WATER_TEMP] = to_signed_16(block_mon_1[10]) / 10.0
            raw_data[REG_SUPPLY_PRESSURE] = block_mon_1[11]
            raw_data[REG_EXTRACT_PRESSURE] = block_mon_1[12]
            raw_data[REG_AIR_QUALITY_TYPE] = block_mon_1[13]
            raw_data[REG_AIR_QUALITY_LEVEL] = block_mon_1[14]
            raw_data[REG_SUPPLY_HUMIDITY] = block_mon_1[15] / 10.0
            raw_data[REG_WATER_HEATER_LEVEL] = block_mon_1[16] / 10.0
            raw_data[REG_WATER_COOLER_LEVEL] = block_mon_1[17] / 10.0
            raw_data[REG_HUMIDITY_CONTROL_LEVEL] = block_mon_1[18] / 10.0
            raw_data[REG_HEAT_EXCHANGER_LEVEL] = block_mon_1[19] / 10.0
            raw_data[REG_RECIRCULATION_LEVEL] = block_mon_1[20] / 10.0
            raw_data[REG_SUPPLY_FAN_LEVEL] = block_mon_1[21] / 10.0
            raw_data[REG_EXHAUST_FAN_LEVEL] = block_mon_1[22] / 10.0

        if block_mon_2:
            raw_data[REG_TEMP_SETPOINT] = to_signed_16(block_mon_2[0]) / 10.0
            raw_data[REG_SUPPLY_TEMP_SETPOINT] = to_signed_16(block_mon_2[1]) / 10.0

        if block_mon_flow_sp:
            raw_data[REG_SUPPLY_FLOW_SETPOINT] = decode_32bit(block_mon_flow_sp[0], block_mon_flow_sp[1])
            raw_data[REG_EXTRACT_FLOW_SETPOINT] = decode_32bit(block_mon_flow_sp[2], block_mon_flow_sp[3])

        if block_mon_3: raw_data[REG_INTERNAL_SUPPLY_TEMP] = to_signed_16(block_mon_3[0]) / 10.0
        if block_mon_4: raw_data[REG_ALARM_DOUT] = block_mon_4[0]

        # Parse Block 7 (Efficiency & SFP)
        if block_efficiency:
            raw_data[REG_EFFICIENCY] = block_efficiency[0] if block_efficiency[0] != 255 else None
            raw_data[REG_ENERGY_SAVING] = block_efficiency[1] if block_efficiency[1] != 255 else None
            raw_data[REG_EXCHANGER_RECOVERY] = decode_32bit(block_efficiency[2], block_efficiency[3])
            raw_data[REG_SUPPLY_SFP] = block_efficiency[4] / 100.0
            raw_data[REG_EXHAUST_SFP] = block_efficiency[5] / 100.0
            raw_data[REG_OUTDOOR_FILTER_IMPURITY] = block_efficiency[6]
            raw_data[REG_EXTRACT_FILTER_IMPURITY] = block_efficiency[7]

        # Parse Block 8 (Filters Dirty Binary flags) safely
        if filter_outdoor: raw_data[REG_OUTDOOR_FILTER_DIRTY] = filter_outdoor[0]
        if filter_extract: raw_data[REG_EXTRACT_FILTER_DIRTY] = filter_extract[0]

        return raw_data

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a value to a Modbus register."""
        wire_address = address - 1  # 0-indexing translation
        _LOGGER.debug("Writing Modbus register %s (wire %s) = %s", address, wire_address, value)
        if not self.client.connected:
            await self.client.connect()
            
        try:
            sig = inspect.signature(self.client.write_register)
            kwargs = {}
            
            if 'device_id' in sig.parameters: kwargs['device_id'] = self.slave_id
            elif 'slave' in sig.parameters: kwargs['slave'] = self.slave_id
            elif 'unit' in sig.parameters: kwargs['unit'] = self.slave_id
            else: kwargs['slave'] = self.slave_id
            
            result = self.client.write_register(wire_address, value, **kwargs)
            if inspect.isawaitable(result):
                await result
                
        except Exception as err:
            _LOGGER.error("Failed to write Modbus register %s: %s", address, err)
            raise
        finally:
            self.hass.async_create_task(self.async_request_refresh())

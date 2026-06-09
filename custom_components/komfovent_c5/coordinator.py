"""Data update coordinator for Komfovent C5 integration."""
from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, timedelta
from typing import Any

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SLAVE_ID,
    DOMAIN,
    REG_AIR_COOLER_HOURS,
    REG_AIR_HEATER_HOURS,
    REG_AIR_HEATER_KWH,
    REG_AIR_QUALITY_LEVEL,
    REG_AIR_QUALITY_TYPE,
    REG_ALARM_COUNT,
    REG_ALARM_DOUT,
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
    REG_ELECTRIC_HEATER_LEVEL,
    REG_ENERGY_SAVING,
    REG_EXCHANGER_RECOVERY,
    REG_EXHAUST_FAN_HOURS,
    REG_EXHAUST_FAN_LEVEL,
    REG_EXHAUST_FAN_POWER,
    REG_EXHAUST_SFP,
    REG_EXHAUST_TEMP,
    REG_EXTRACT_FILTER_DIRTY,
    REG_EXTRACT_FILTER_IMPURITY,
    REG_EXTRACT_FLOW_SETPOINT,
    REG_EXTRACT_PRESSURE,
    REG_EXTRACT_TEMP,
    REG_FLOW_CONTROL_MODE,
    REG_HEAT_EXCHANGER_KWH,
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
    REG_RTC_DATE,
    REG_RTC_SECONDS,
    REG_RTC_TIME,
    REG_RTC_YEAR,
    REG_SPECIAL_EXTRACT_FLOW,
    REG_SPECIAL_SUPPLY_FLOW,
    REG_SPECIAL_TEMP,
    REG_STATUS,
    REG_SUMMER_COOLING,
    REG_SUPPLY_FAN_HOURS,
    REG_SUPPLY_FAN_LEVEL,
    REG_SUPPLY_FAN_POWER,
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
    if val >= 0x8000:
        return val - 0x10000
    return val

def decode_32bit(reg_high: int, reg_low: int) -> int:
    return (reg_high << 16) + reg_low

def encode_32bit(val: int) -> list[int]:
    return [(val >> 16) & 0xFFFF, val & 0xFFFF]

def parse_counter(high: int, low: int) -> int | None:
    """Parse 32-bit counter and return None if unavailable (0xFFFFFFFF)."""
    val = decode_32bit(high, low)
    if val == 4294967295:  # 0xFFFFFFFF
        return None
    return val

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
        self.client = AsyncModbusTcpClient(host=host, port=port, timeout=5.0)
        self.slave_id = slave_id
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
        _LOGGER.debug("Connecting to Modbus TCP server %s:%s", self.host, self.port)
        try:
            connected = await self.client.connect()
            if not connected:
                raise UpdateFailed("Failed to establish Modbus TCP connection")

            raw_data: dict[int | str, Any] = {}

            async def _read_block(address: int, count: int) -> list[int] | None:
                wire_address = address - 1 
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
                        _LOGGER.debug("Modbus read returned error at address %s: %s", address, result)
                        return None
                    return result.registers
                except Exception as err:
                    _LOGGER.debug("Exception reading Modbus block starting at %s: %s", address, err)
                    return None

            block_rtc = await _read_block(REG_RTC_TIME, 5)
            await asyncio.sleep(0.3)
            block_on_off = await _read_block(REG_ON_OFF, 1)
            await asyncio.sleep(0.3)
            block_modes = await _read_block(100, 29)
            await asyncio.sleep(0.3)
            block_override = await _read_block(REG_OVERRIDE_ENABLE, 9)
            await asyncio.sleep(0.3)
            heater_water = await _read_block(REG_WATER_HEATER, 1)
            await asyncio.sleep(0.3)
            heater_cooler = await _read_block(REG_WATER_COOLER, 1)
            await asyncio.sleep(0.3)
            heater_electric = await _read_block(REG_ELECTRIC_HEATER, 1)
            await asyncio.sleep(0.3)
            block_alarms = await _read_block(REG_ALARM_COUNT, 11)
            await asyncio.sleep(0.3)
            
            block_mon_1 = await _read_block(2000, 24)       
            await asyncio.sleep(0.3)
            block_elec_heater_level = await _read_block(REG_ELECTRIC_HEATER_LEVEL, 1)
            await asyncio.sleep(0.3)
            block_mon_2 = await _read_block(2032, 2)        
            await asyncio.sleep(0.3)
            block_mon_flow_sp = await _read_block(2036, 4)  
            await asyncio.sleep(0.3)
            block_mon_3 = await _read_block(2040, 1)        
            await asyncio.sleep(0.3)
            block_mon_4 = await _read_block(2045, 1)        
            await asyncio.sleep(0.3)
            
            # WIDENED TO 23 REGISTERS TO CAPTURE LIFETIME COUNTERS (2201 - 2223)
            block_efficiency = await _read_block(REG_EFFICIENCY, 23)
            await asyncio.sleep(0.3)
            
            filter_outdoor = await _read_block(REG_OUTDOOR_FILTER_DIRTY, 1)
            await asyncio.sleep(0.3)
            filter_extract = await _read_block(REG_EXTRACT_FILTER_DIRTY, 1)

            if block_on_off is None or block_mon_1 is None:
                raise UpdateFailed("Critical Modbus data blocks could not be read")

            if block_rtc:
                hour = (block_rtc[0] >> 8) & 0xFF
                minute = block_rtc[0] & 0xFF
                month = (block_rtc[3] >> 8) & 0xFF
                day = block_rtc[3] & 0xFF
                year = block_rtc[4]
                if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                    raw_data["rtc_time"] = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
                    raw_data["rtc_year"] = year
                    raw_data["rtc_month"] = month
                    raw_data["rtc_day"] = day

            raw_data[REG_ON_OFF] = block_on_off[0]

            if block_modes:
                raw_data[100] = block_modes[0]  
                raw_data[REG_COMFORT1_TEMP] = block_modes[5]
                raw_data[REG_COMFORT2_TEMP] = block_modes[10]
                raw_data[REG_ECONOMY1_TEMP] = block_modes[15]
                raw_data[REG_ECONOMY2_TEMP] = block_modes[20]
                raw_data[REG_SPECIAL_SUPPLY_FLOW] = decode_32bit(block_modes[21], block_modes[22])
                raw_data[REG_SPECIAL_EXTRACT_FLOW] = decode_32bit(block_modes[23], block_modes[24])
                raw_data[REG_SPECIAL_TEMP] = block_modes[25]
                raw_data[REG_FLOW_CONTROL_MODE] = block_modes[27]
                raw_data[REG_TEMP_CONTROL_MODE] = block_modes[28]

            if block_override:
                raw_data[REG_OVERRIDE_ENABLE] = block_override[0]
                raw_data[REG_OVERRIDE_TYPE] = block_override[1]
                raw_data[REG_OVERRIDE_MODE] = block_override[2]
                raw_data[REG_SUMMER_COOLING] = block_override[3]
                raw_data[REG_DEMAND_CONTROL] = block_override[5]
                raw_data[REG_RECIRC_CONTROL] = block_override[7]

            if heater_water: raw_data[REG_WATER_HEATER] = heater_water[0]
            if heater_cooler: raw_data[REG_WATER_COOLER] = heater_cooler[0]
            if heater_electric: raw_data[REG_ELECTRIC_HEATER] = heater_electric[0]

            if block_alarms:
                raw_data[REG_ALARM_COUNT] = block_alarms[0]
                raw_data["alarm_codes"] = [code for code in block_alarms[1:] if code != 0]

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

            if block_elec_heater_level: 
                raw_data[REG_ELECTRIC_HEATER_LEVEL] = block_elec_heater_level[0] / 10.0

            if block_mon_2:
                raw_data[REG_TEMP_SETPOINT] = to_signed_16(block_mon_2[0]) / 10.0
                raw_data[REG_SUPPLY_TEMP_SETPOINT] = to_signed_16(block_mon_2[1]) / 10.0

            if block_mon_flow_sp:
                raw_data[REG_SUPPLY_FLOW_SETPOINT] = decode_32bit(block_mon_flow_sp[0], block_mon_flow_sp[1])
                raw_data[REG_EXTRACT_FLOW_SETPOINT] = decode_32bit(block_mon_flow_sp[2], block_mon_flow_sp[3])

            if block_mon_3: raw_data[REG_INTERNAL_SUPPLY_TEMP] = to_signed_16(block_mon_3[0]) / 10.0
            if block_mon_4: raw_data[REG_ALARM_DOUT] = block_mon_4[0]

            # Parse Block 7 (Efficiency, SFP, and Extended Counters)
            if block_efficiency and len(block_efficiency) >= 23:
                raw_data[REG_EFFICIENCY] = 0 if block_efficiency[0] == 255 else block_efficiency[0]
                raw_data[REG_ENERGY_SAVING] = 0 if block_efficiency[1] == 255 else block_efficiency[1]
                
                # Exchanger Recovery can sometimes return 0xFFFFFFFF if unavailable
                raw_data[REG_EXCHANGER_RECOVERY] = parse_counter(block_efficiency[2], block_efficiency[3])
                
                raw_data[REG_SUPPLY_SFP] = block_efficiency[4] / 100.0
                raw_data[REG_EXHAUST_SFP] = block_efficiency[5] / 100.0
                raw_data[REG_OUTDOOR_FILTER_IMPURITY] = block_efficiency[6]
                raw_data[REG_EXTRACT_FILTER_IMPURITY] = block_efficiency[7]

                # --- NEW COUNTERS ---
                raw_data[REG_AIR_HEATER_HOURS] = parse_counter(block_efficiency[8], block_efficiency[9])
                raw_data[REG_SUPPLY_FAN_HOURS] = parse_counter(block_efficiency[10], block_efficiency[11])
                raw_data[REG_EXHAUST_FAN_HOURS] = parse_counter(block_efficiency[12], block_efficiency[13])
                raw_data[REG_SUPPLY_FAN_POWER] = block_efficiency[14]
                raw_data[REG_EXHAUST_FAN_POWER] = block_efficiency[15]
                # Index 16 is Active Functions (omitted per user scope)
                raw_data[REG_AIR_COOLER_HOURS] = parse_counter(block_efficiency[17], block_efficiency[18])
                raw_data[REG_HEAT_EXCHANGER_KWH] = parse_counter(block_efficiency[19], block_efficiency[20])
                raw_data[REG_AIR_HEATER_KWH] = parse_counter(block_efficiency[21], block_efficiency[22])

            if filter_outdoor: raw_data[REG_OUTDOOR_FILTER_DIRTY] = filter_outdoor[0]
            if filter_extract: raw_data[REG_EXTRACT_FILTER_DIRTY] = filter_extract[0]

            return raw_data
        except Exception as err:
            raise UpdateFailed(f"Modbus error during update: {err}") from err
        finally:
            self.client.close()

    async def async_write_register(self, address: int, value: int) -> None:
        wire_address = address - 1  
        _LOGGER.debug("Writing Modbus register %s (wire %s) = %s", address, wire_address, value)
        try:
            await self.client.connect()
            sig = inspect.signature(self.client.write_register)
            kwargs = {}
            if 'device_id' in sig.parameters: kwargs['device_id'] = self.slave_id
            elif 'slave' in sig.parameters: kwargs['slave'] = self.slave_id
            elif 'unit' in sig.parameters: kwargs['unit'] = self.slave_id
            else: kwargs['slave'] = self.slave_id
            
            result = self.client.write_register(wire_address, value, **kwargs)
            if inspect.isawaitable(result): await result
        except Exception as err:
            _LOGGER.error("Failed to write Modbus register %s: %s", address, err)
            raise
        finally:
            self.client.close()
            self.hass.async_create_task(self.async_request_refresh())

    async def async_write_registers(self, address: int, values: list[int]) -> None:
        wire_address = address - 1  
        _LOGGER.debug("Writing Modbus registers %s (wire %s) = %s", address, wire_address, values)
        try:
            await self.client.connect()
            sig = inspect.signature(self.client.write_registers)
            kwargs = {}
            if 'device_id' in sig.parameters: kwargs['device_id'] = self.slave_id
            elif 'slave' in sig.parameters: kwargs['slave'] = self.slave_id
            elif 'unit' in sig.parameters: kwargs['unit'] = self.slave_id
            else: kwargs['slave'] = self.slave_id
            
            result = self.client.write_registers(wire_address, values, **kwargs)
            if inspect.isawaitable(result): await result
        except Exception as err:
            _LOGGER.error("Failed to write Modbus registers %s: %s", address, err)
            raise
        finally:
            self.client.close()
            self.hass.async_create_task(self.async_request_refresh())

    async def async_sync_time(self) -> None:
        now = datetime.now()
        time_reg = (now.hour << 8) | now.minute
        sec_reg = now.second
        
        _LOGGER.info("Syncing Komfovent RTC Time to: %02d:%02d:%02d", now.hour, now.minute, now.second)
        await self.async_write_register(REG_RTC_TIME, time_reg)
        await asyncio.sleep(0.1)
        await self.async_write_register(REG_RTC_SECONDS, sec_reg)

        current_data = self.data or {}
        c_year = current_data.get("rtc_year")
        c_month = current_data.get("rtc_month")
        c_day = current_data.get("rtc_day")

        if c_year != now.year or c_month != now.month or c_day != now.day:
            _LOGGER.info("Syncing Komfovent RTC Date to: %04d-%02d-%02d", now.year, now.month, now.day)
            date_reg = (now.month << 8) | now.day
            year_reg = now.year
            
            await asyncio.sleep(0.1)
            await self.async_write_register(REG_RTC_DATE, date_reg)
            await asyncio.sleep(0.1)
            await self.async_write_register(REG_RTC_YEAR, year_reg)

    async def async_reset_alarms(self) -> None:
        _LOGGER.warning("Resetting Komfovent alarms and filter statuses via Modbus...")
        await self.async_write_register(REG_OUTDOOR_FILTER_DIRTY, 0)
        await asyncio.sleep(0.1)
        await self.async_write_register(REG_EXTRACT_FILTER_DIRTY, 0)
        await asyncio.sleep(0.1)
        await self.async_write_register(REG_ALARM_COUNT, 0x99C5)

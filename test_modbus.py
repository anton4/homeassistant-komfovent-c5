#!/usr/bin/env python3
"""CLI utility to test Modbus TCP connection to Komfovent C5 and print decoded values."""
import os
import sys

# Prevent local select.py in same directory from shadowing standard library modules
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path = [p for p in sys.path if p and os.path.realpath(p) != script_dir]

import argparse
import asyncio
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient

# Setup simple logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
_LOGGER = logging.getLogger(__name__)

# Constants matching const.py
ALARM_MAP = {
    1: "Low supply air flow",
    2: "Low extract air flow",
    3: "VAV calibration fail",
    4: "Change outdoor air filter",
    5: "Change extract air filter",
    12: "High pressure on compressor",
    13: "Low pressure on compressor",
    14: "Service time",
    15: "Evaporator icing",
    16: "Heat pump malfunction",
    17: "Heat pump malfunction",
    18: "Heat pump malfunction",
    19: "Compressor off",
    20: "Compressor off",
    21: "High pressure on compressor",
    22: "Low pressure on compressor",
    44: "Heat pump malfunction or Communication error",
    59: "Heat pump malfunction or Communication error",
    83: "Heat pump malfunction or Communication error",
    95: "Low heat exchanger efficiency",
    97: "Communication error",
    99: "Communication error",
    112: "Water pump/coil alarm",
    113: "CF or HP exchanger not calibrated",
    114: "CF or HP exchanger not calibrated",
    115: "High pressure on compressor",
    116: "Low pressure on compressor",
    126: "Unknown alarm",
    127: "Service mode",
    128: "Supply air temp. Sensor failure",
    129: "Supply air temp. Sensor failure",
    130: "Extract air temp. Sensor failure",
    131: "Extract air temp. Sensor failure",
    132: "Outdoor air temp. Sensor failure",
    133: "Outdoor air temp. Sensor failure",
    134: "Exhaust air temp. Sensor failure",
    135: "Exhaust air temp. Sensor failure",
    136: "Water temp. sensor failure",
    137: "Water temp. sensor failure",
    138: "Return water temp. low",
    139: "Internal fire alarm",
    140: "External fire alarm",
    141: "External stop",
    142: "Heat exchanger failure",
    143: "Heat exchanger icing",
    144: "Low supply air temperature",
    145: "High supply air temperature",
    146: "Low supply air flow",
    147: "Low extract air flow",
    149: "Electric heater overheat",
    152: "Evaporator air temp. Sensor failure",
    153: "Evaporator coil temp. Sensor failure",
    156: "Compressor failure",
    170: "External stop",
    172: "Water pump/coil alarm",
    173: "CF exchanger not calibrated",
    210: "Controller failure",
    211: "Communication error",
    217: "Service mode",
    226: "Supply fan drive failure",
    227: "Supply fan drive overload",
    228: "Supply fan motor failure",
    230: "Supply fan motor overload",
    231: "Exhaust fan drive failure",
    232: "Exhaust fan drive oveload",
    233: "Exhaust fan motor failure",
    234: "Exhaust fan motor overload",
    236: "Rotor drive failure",
    237: "Rotor drive overload",
    238: "Rotor motor failure",
    239: "Rotor motor overload",
}

def to_signed_16(val: int) -> int:
    if val >= 0x8000:
        return val - 0x10000
    return val

def decode_32bit(reg_high: int, reg_low: int) -> int:
    return (reg_high << 16) + reg_low

async def read_holding_registers_compatible(client: AsyncModbusTcpClient, address: int, count: int, slave_id: int):
    """Compatible register reader supporting slave, unit, and device_id keywords."""
    try:
        # Try device_id (newer pymodbus e.g. 3.13+)
        result = await client.read_holding_registers(address, count, device_id=slave_id)
        return result
    except TypeError:
        try:
            # Try slave (older pymodbus 3.x)
            result = await client.read_holding_registers(address, count, slave=slave_id)
            return result
        except TypeError:
            # Try unit (pymodbus 2.x)
            result = await client.read_holding_registers(address, count, unit=slave_id)
            return result

async def main():
    parser = argparse.ArgumentParser(description="Test Modbus TCP connection to Komfovent C5.")
    parser.add_argument("--host", required=True, help="IP address or hostname of the unit")
    parser.add_argument("--port", type=int, default=502, help="Modbus TCP port (default: 502)")
    parser.add_argument("--slave-id", type=int, default=1, help="Modbus Slave/Unit/Device ID (default: 1)")
    args = parser.parse_args()

    print(f"Connecting to {args.host}:{args.port} using Slave ID {args.slave_id}...")
    client = AsyncModbusTcpClient(host=args.host, port=args.port)
    
    connected = await client.connect()
    if not connected:
        print("ERROR: Failed to connect to Modbus TCP client!")
        sys.exit(1)

    print("Connected successfully. Reading registers...")
    
    # Helper to print reads
    async def read_block(name: str, address: int, count: int):
        try:
            result = await read_holding_registers_compatible(client, address, count, args.slave_id)
            if result.isError():
                print(f"  {name}: Read Error -> {result}")
                return None
            return result.registers
        except Exception as e:
            print(f"  {name}: Exception occurred -> {e}")
            return None

    # Read blocks
    b1 = await read_block("Block 1 (On/Off)", 1, 1)
    b2 = await read_block("Block 2 (Modes)", 100, 29)
    b3 = await read_block("Block 3 (Override)", 512, 9)
    b4 = await read_block("Block 4 (Heaters)", 551, 3)
    b5 = await read_block("Block 5 (Alarms)", 1000, 11)
    b6 = await read_block("Block 6 (Monitoring)", 2000, 48)
    b7 = await read_block("Block 7 (Efficiency)", 2201, 8)
    b8 = await read_block("Block 8 (Filters dirty)", 2852, 2)

    client.close()

    print("\n" + "=" * 50)
    print("DECODED DATA SUMMARY:")
    print("=" * 50)

    if b1:
        print(f"AHU On/Off Switch state (Reg 1): {'ON' if b1[0] == 1 else 'OFF'} ({b1[0]})")
    
    if b2:
        modes = {1: "Comfort 1", 2: "Comfort 2", 3: "Economy 1", 4: "Economy 2", 5: "Special", 6: "Program"}
        print(f"Selected Mode (Reg 100): {modes.get(b2[0], f'Unknown ({b2[0]})')}")
        print(f"Comfort 1 Temp Setpoint (Reg 105): {b2[5] / 10.0} °C")
        print(f"Comfort 2 Temp Setpoint (Reg 110): {b2[10] / 10.0} °C")
        print(f"Economy 1 Temp Setpoint (Reg 115): {b2[15] / 10.0} °C")
        print(f"Economy 2 Temp Setpoint (Reg 120): {b2[20] / 10.0} °C")
        print(f"Special Temp Setpoint (Reg 125): {b2[25] / 10.0} °C")
        print(f"Flow Control Mode (Reg 127): {['CAV', 'VAV', 'DCV'][b2[27]] if b2[27] < 3 else b2[27]}")
        print(f"Temp Control Mode (Reg 128): {['Supply', 'Extract', 'Room'][b2[28]] if b2[28] < 3 else b2[28]}")

    if b3:
        print(f"Override Mode Enable (Reg 512): {'ENABLED' if b3[0] == 1 else 'DISABLED'}")
        print(f"Summer Night Cooling Enable (Reg 515): {'ENABLED' if b3[3] == 1 else 'DISABLED'}")
        print(f"Operation on Demand Enable (Reg 517): {'ENABLED' if b3[5] == 1 else 'DISABLED'}")
        print(f"Recirculation Control Enable (Reg 519): {'ENABLED' if b3[7] == 1 else 'DISABLED'}")

    if b4:
        print(f"Water Heater Enable (Reg 551): {'ENABLED' if b4[0] == 1 else 'DISABLED'}")
        print(f"Water Cooler Enable (Reg 552): {'ENABLED' if b4[1] == 1 else 'DISABLED'}")
        print(f"Electric Heater Enable (Reg 553): {'ENABLED' if b4[2] == 1 else 'DISABLED'}")

    if b5:
        print(f"Active Alarms Count (Reg 1000): {b5[0]}")
        active_codes = [c for c in b5[1:] if c != 0]
        print(f"Active Alarm Codes: {active_codes}")
        for code in active_codes:
            print(f"  - Alarm {code}: {ALARM_MAP.get(code, 'Unknown Alarm')}")

    if b6:
        status_map = {0: "Stopped", 1: "Idle (Fans Stopped)", 2: "Running"}
        print(f"Current Status (Reg 2000): {status_map.get(b6[0], f'Unknown ({b6[0]})')}")
        print(f"Current Mode (Reg 2001): {b6[1]}")
        print(f"Current Supply Flow (Reg 2002-2003): {decode_32bit(b6[2], b6[3])} m3/h")
        print(f"Current Exhaust Flow (Reg 2004-2005): {decode_32bit(b6[4], b6[5])} m3/h")
        print(f"Supply Temp (Reg 2006): {to_signed_16(b6[6]) / 10.0} °C")
        print(f"Extract Temp (Reg 2007): {to_signed_16(b6[7]) / 10.0} °C")
        print(f"Outdoor Temp (Reg 2008): {to_signed_16(b6[8]) / 10.0} °C")
        print(f"Exhaust Temp (Reg 2009): {to_signed_16(b6[9]) / 10.0} °C")
        print(f"Return Water Temp (Reg 2010): {to_signed_16(b6[10]) / 10.0} °C")
        print(f"Supply Air Pressure (Reg 2011): {b6[11]} Pa")
        print(f"Extract Air Pressure (Reg 2012): {b6[12]} Pa")
        print(f"Supply Humidity (Reg 2015): {b6[15] / 10.0} %")
        print(f"Water Heater Level (Reg 2016): {b6[16] / 10.0} %")
        print(f"Water Cooler Level (Reg 2017): {b6[17] / 10.0} %")
        print(f"Heat Exchanger Level (Reg 2019): {b6[19] / 10.0} %")
        print(f"Supply Fan Level (Reg 2021): {b6[21] / 10.0} %")
        print(f"Exhaust Fan Level (Reg 2022): {b6[22] / 10.0} %")
        print(f"Temp Setpoint (Reg 2032): {to_signed_16(b6[32]) / 10.0} °C")
        print(f"Supply Temp Setpoint (Reg 2033): {to_signed_16(b6[33]) / 10.0} °C")
        print(f"Internal Supply Temp (Reg 2040): {to_signed_16(b6[40]) / 10.0} °C")
        print(f"Alarm DOUT State (Reg 2045): {b6[45]}")

    if b7:
        print(f"Thermal Efficiency (Reg 2201): {b7[0] if b7[0] != 255 else 'N/A'} %")
        print(f"Energy Saving (Reg 2202): {b7[1] if b7[1] != 255 else 'N/A'} %")
        print(f"Exchanger Recovery Power (Reg 2203-2204): {decode_32bit(b7[2], b7[3])} W")
        print(f"Supply SFP (Reg 2205): {b7[4] / 100.0} kW/(m3/s)")
        print(f"Exhaust SFP (Reg 2206): {b7[5] / 100.0} kW/(m3/s)")
        print(f"Outdoor Filter Impurity (Reg 2207): {b7[6]} %")
        print(f"Extract Filter Impurity (Reg 2208): {b7[7]} %")

    if b8:
        print(f"Outdoor Filter (Reg 2852): {'DIRTY' if b8[0] == 1 else 'CLEAN'}")
        print(f"Extract Filter (Reg 2853): {'DIRTY' if b8[1] == 1 else 'CLEAN'}")
        
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())

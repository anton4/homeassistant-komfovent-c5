"""Constants for the Komfovent C5 integration."""
from homeassistant.const import Platform

DOMAIN = "komfovent_c5"
DEFAULT_NAME = "Komfovent C5"
DEFAULT_PORT = 502
DEFAULT_SCAN_INTERVAL = 30

CONF_SLAVE_ID = "slave_id"

PLATFORMS = [Platform.CLIMATE, Platform.NUMBER, Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]

# Modbus registers map (C5 controller)
# Write registers (Holding registers)
REG_ON_OFF = 1                  # 0: Off, 1: On
REG_MODE_SELECT = 100           # 1: Comfort1, 2: Comfort2, 3: Economy1, 4: Economy2, 5: Special, 6: Program

# Master Clock (RTC) Registers (C5)
REG_RTC_TIME = 450              # MSB=Hour, LSB=Minute
REG_RTC_SECONDS = 451           # 0-59
REG_RTC_DATE = 453              # MSB=Month, LSB=Day
REG_RTC_YEAR = 454              # Year (e.g., 2026)

# Preset target temperatures
REG_COMFORT1_TEMP = 105         # x10
REG_COMFORT2_TEMP = 110         # x10
REG_ECONOMY1_TEMP = 115         # x10
REG_ECONOMY2_TEMP = 120         # x10
REG_SPECIAL_TEMP = 125          # x10

# Special Mode Flows (32-bit registers)
REG_SPECIAL_SUPPLY_FLOW = 121   # 32-bit (121-122)
REG_SPECIAL_EXTRACT_FLOW = 123  # 32-bit (123-124)

REG_FLOW_CONTROL_MODE = 127     # 0: CAV, 1: VAV, 2: DCV
REG_TEMP_CONTROL_MODE = 128     # 0: Supply, 1: Extract, 2: Room

# Functions settings
REG_OVERRIDE_ENABLE = 512       # 0: Disable, 1: Enable
REG_OVERRIDE_TYPE = 513         # 0: All time, 1: If on, 2: If off
REG_OVERRIDE_MODE = 514         # 0-6: Modes
REG_SUMMER_COOLING = 515        # 0: Disable, 1: Enable
REG_DEMAND_CONTROL = 517        # 0: Disable, 1: Enable
REG_RECIRC_CONTROL = 519        # 0: Disable, 1: Enable

# Heaters/coolers enables
REG_WATER_HEATER = 551          # 0: Disable, 1: Enable
REG_WATER_COOLER = 552          # 0: Disable, 1: Enable
REG_ELECTRIC_HEATER = 553       # 0: Disable, 1: Enable

# Alarms
REG_ALARM_COUNT = 1000          # 0..10
REG_ALARM_START = 1001          # 1001-1010 active alarm codes

# Monitoring data
REG_STATUS = 2000               # 0: Stop, 1: Enabled but fans stopped, 2: Running
REG_CURRENT_MODE = 2001         # 0: Standby, 1: Comfort1, 2: Comfort2, 3: Economy1, 4: Economy2, 5: Special
REG_CURRENT_SUPPLY_FLOW = 2002  # 32-bit (2002-2003) m3/h, m3/s, or l/s
REG_CURRENT_EXHAUST_FLOW = 2004 # 32-bit (2004-2005) m3/h, m3/s, or l/s
REG_SUPPLY_TEMP = 2006          # x10
REG_EXTRACT_TEMP = 2007         # x10
REG_OUTDOOR_TEMP = 2008         # x10
REG_EXHAUST_TEMP = 2009         # x10
REG_RETURN_WATER_TEMP = 2010    # x10
REG_SUPPLY_PRESSURE = 2011      # Pa
REG_EXTRACT_PRESSURE = 2012     # Pa
REG_AIR_QUALITY_TYPE = 2013     # 0-CO2, 1-VOCq, 2-VOCp, 3-RH, 4-TMP
REG_AIR_QUALITY_LEVEL = 2014    # ppm, %, etc.
REG_SUPPLY_HUMIDITY = 2015      # x10 %
REG_WATER_HEATER_LEVEL = 2016   # 0..100%
REG_WATER_COOLER_LEVEL = 2017   # 0..100%
REG_HUMIDITY_CONTROL_LEVEL = 2018 # 0..100%
REG_HEAT_EXCHANGER_LEVEL = 2019 # 0..100%
REG_RECIRCULATION_LEVEL = 2020  # 0..100%
REG_SUPPLY_FAN_LEVEL = 2021     # 0..100%
REG_EXHAUST_FAN_LEVEL = 2022    # 0..100%
REG_ELECTRIC_HEATER_LEVEL = 2025 # 0..100%
REG_TEMP_SETPOINT = 2032        # x10 current temperature setpoint
REG_SUPPLY_TEMP_SETPOINT = 2033 # x10 current supply temp setpoint
REG_SUPPLY_FLOW_SETPOINT = 2036 # 32-bit (2036-2037)
REG_EXTRACT_FLOW_SETPOINT = 2038 # 32-bit (2038-2039)
REG_INTERNAL_SUPPLY_TEMP = 2040 # x10
REG_ALARM_DOUT = 2045           # 0: No alarms, 1: Active alarms

# Counters and Efficiencies
REG_EFFICIENCY = 2201           # %
REG_ENERGY_SAVING = 2202        # %
REG_EXCHANGER_RECOVERY = 2203   # 32-bit (2203-2204) W
REG_SUPPLY_SFP = 2205           # x100
REG_EXHAUST_SFP = 2206          # x100
REG_OUTDOOR_FILTER_IMPURITY = 2207 # %
REG_EXTRACT_FILTER_IMPURITY = 2208 # %

# New Lifetime Counters (from 2209 - 2223)
REG_AIR_HEATER_HOURS = 2209     # 32-bit (2209-2210) hours
REG_SUPPLY_FAN_HOURS = 2211     # 32-bit (2211-2212) hours
REG_EXHAUST_FAN_HOURS = 2213    # 32-bit (2213-2214) hours
REG_SUPPLY_FAN_POWER = 2215     # 16-bit W
REG_EXHAUST_FAN_POWER = 2216    # 16-bit W
REG_AIR_COOLER_HOURS = 2218     # 32-bit (2218-2219) hours
REG_HEAT_EXCHANGER_KWH = 2220   # 32-bit (2220-2221) kWh
REG_AIR_HEATER_KWH = 2222       # 32-bit (2222-2223) kWh

# Service binary filters
REG_OUTDOOR_FILTER_DIRTY = 2852 # 0: Clean, 1: Dirty
REG_EXTRACT_FILTER_DIRTY = 2853 # 0: Clean, 1: Dirty

# Mode mappings
PRESET_STANDBY = "standby"
PRESET_COMFORT1 = "comfort1"
PRESET_COMFORT2 = "comfort2"
PRESET_ECONOMY1 = "economy1"
PRESET_ECONOMY2 = "economy2"
PRESET_SPECIAL = "special"
PRESET_PROGRAM = "program"

PRESET_TO_REG = {
    PRESET_COMFORT1: 1,
    PRESET_COMFORT2: 2,
    PRESET_ECONOMY1: 3,
    PRESET_ECONOMY2: 4,
    PRESET_SPECIAL: 5,
    PRESET_PROGRAM: 6,
}

REG_TO_PRESET = {
    0: PRESET_STANDBY,
    1: PRESET_COMFORT1,
    2: PRESET_COMFORT2,
    3: PRESET_ECONOMY1,
    4: PRESET_ECONOMY2,
    5: PRESET_SPECIAL,
    6: PRESET_PROGRAM,
}

MODE_TO_SETPOINT_REG = {
    1: REG_COMFORT1_TEMP,
    2: REG_COMFORT2_TEMP,
    3: REG_ECONOMY1_TEMP,
    4: REG_ECONOMY2_TEMP,
    5: REG_SPECIAL_TEMP,
    0: REG_COMFORT1_TEMP,
    6: REG_COMFORT1_TEMP,
}

# Komfovent C5 Custom Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/anton4/homeassistant-komfovent-c5)](https://github.com/anton4/homeassistant-komfovent-c5/releases)
![HACS Support](https://img.shields.io/badge/HACS-Custom-orange.svg)

A robust, local-polling Home Assistant custom component to monitor and control **Komfovent** ventilation units equipped with the **C5 Controller** via **Modbus TCP**.

<img width="765" height="1024" alt="d835de52-ad9d-46a9-a22b-9828a05159e3" src="https://github.com/user-attachments/assets/215ad3fe-34cc-4209-bd62-58cf023d8cbd" />


Unlike generic Modbus templates, this integration is purpose-built for the Komfovent C5 memory map. It handles the controller's specific network polling limits, translates standard Home Assistant climate entities into Komfovent preset modes, and dynamically handles unmapped hardware (like missing heaters) without crashing.

## ✨ Features

* **🌡️ Climate Control:** 
    * Turn the AHU On/Off.
    * View and set the target temperature.
    * View and set Special mode Supply/Extract flows (m³/h)
    * Clear alarms
    * Clean air filters calibration
    * Change active preset modes (`Comfort 1`, `Comfort 2`, `Economy 1`, `Economy 2`, `Special`, `Program`).
    * **Temperature Control Mode Selection:** A clean dropdown menu to dynamically change which thermostat configuration the unit tracks (`Supply Air`, `Extract Air`, or `Room Control`).

* **📊 Comprehensive Monitoring (Sensors):**
    * **Airflow:** Supply/Extract flows (m³/h), Fan levels (%), and pressures (Pa).
    * **Temperatures:** Supply, Extract, Outdoor, Exhaust, Return Water, and Internal temperatures.
    * **Efficiency:** Thermal efficiency, energy savings, heat exchanger recovery power (W), and Specific Fan Power (SFP).
    * **Maintenance:** Filter impurity levels (%), filter clean/dirty binary states, active alarm states/codes, and service time counter.
    * **🔋 Lifetime Counters & Energy Metrics:** Hardware counters tracking lifetime metrics:
        * Supply / Exhaust Fan running hours.
        * Air Heater / Air Cooler running hours.
        * Heat Exchanger total recovered energy (kWh).
        * Air Heater total consumed energy (kWh).
        * Active real-time electrical power usage for both fans (W).

* **🎛️ Feature Switches:**
    * **Standard Features:** Toggle Override functions, Summer Night Cooling, Operation on Demand, and Recirculation.
    * **Hardware Enables:** Enable/Disable Water Heaters, Water Coolers, and Electric Heaters.
    * **⚙️ Special Mode Permissions (Bitmask Config):** Individual toggles to grant or deny hardware permissions exclusively during `Special` mode operation:
        * Special Mode: Heating Enable
        * Special Mode: Cooling Enable
        * Special Mode: Recirculation Enable
        * Special Mode: Humidifying Enable
        * Special Mode: Dehumidifying Enable

* **🛠️ Maintenance & Service Controls (Buttons):**
    * **Sync Clock to HA:** Synchronizes the internal Real-Time Clock (RTC) date and time of the C5 controller to match your Home Assistant server.
    * **Calibrate Clean Filters:** Triggers the native C5 clean air filters pressure calibration sequence. Run this whenever you insert fresh filters to prevent false dirty filter alarms.
    * **Reset Alarms:** Clears the active alarm log and resets the dirty filter flags via a secure Modbus override block.
    * **Reset Operation Counters:** Resets lifetime fan/heater run hour metrics back to zero following major mechanical overhauls.
    * **Reset Service Timer:** Resets the maintenance countdown timer back to 100%.

## ⚠️ Prerequisites

1. Your Komfovent C5 unit must be connected to your local network via Ethernet.
2. **Modbus TCP** must be enabled in the C5 controller's network settings.
3. You need the IP address of your unit and the Modbus port (default is `502`).

## 📦 Installation

### Option 1: Via HACS (Recommended)
1. Open Home Assistant and navigate to **HACS**.
2. Click on the 3 dots in the top right corner and select **Custom repositories**.
3. Add the URL of this GitHub repository.
4. Select **Integration** as the category and click **Add**.
5. Close the modal, search for **Komfovent C5** in HACS, and click **Download**.
6. **Restart Home Assistant.**

### Option 2: Manual Installation
1. Download the `komfovent_c5` folder from this repository.
2. Copy the folder into your Home Assistant's `custom_components/` directory.
3. **Restart Home Assistant.**

## ⚙️ Configuration

Setup is done entirely via the Home Assistant UI.

1. Go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **Komfovent C5**.
4. Enter your configuration details:
    * **Host:** The IP address of your C5 unit (e.g., `192.168.1.50`).
    * **Port:** The Modbus TCP port (default is `502`).
    * **Slave ID:** The Modbus Slave/Unit ID (default is `1`).
5. Click **Submit**.

## 📖 Feature Deeper Dive

### Summer Night Cooling (SNC)
A passive cooling feature that saves energy during summer. When enabled, if the indoor temperature is warm but the outside nighttime temperature drops within favorable thresholds between **00:00 and 06:00**, the controller automatically bypasses heat recovery (halting a rotary wheel or opening a physical plate bypass valve). This flushes your home with filtered, cool night air without activating power-hungry air conditioning.

### Special Mode Configuration
While presets like `Comfort` or `Economy` use automation logic to maintain temperatures, `Special` mode functions as a highly customizable sandbox environment. The provided `Special Mode: *` toggle entities allow you to restrict which hardware components are permitted to activate while the unit runs this preset. For instance, toggling off *Heating Enable* under Special Mode creates an ultra-efficient, ventilation-only preset that locks out the electrical heater entirely.

## 🛠️ Technical Details & Known Behaviors

* **Polling Limits:** The Komfovent C5 network processor is relatively slow. This integration intentionally injects a `300ms` delay between sequential Modbus block reads to prevent overwhelming the controller and causing connection drops.
* **Safe Memory Chunking:** Depending on your specific hardware (e.g., whether you have electric heaters or specific temperature sensors installed), the C5 controller may completely unmap certain Modbus registers. This integration reads memory in small, logical chunks so that a missing hardware feature simply disables that specific entity rather than failing the entire update loop.

## 🐛 Troubleshooting

* **Failed to connect:** Verify that Modbus TCP is enabled on the C5 controller's screen and that your Home Assistant instance is on the same local subnet as the unit.
* **Missing Entities (Unavailable):** If certain switches (like Electric Heater) or sensors are unavailable, it simply means your specific physical machine does not have those features mapped in its firmware or lacks the physical hardware add-ons (such as duct chillers or external humidifiers). These entities can safely be disabled or hidden from your dashboard view.

---
*Disclaimer: This integration is not officially affiliated with or endorsed by Komfovent. Use at your own risk.*

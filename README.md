# Komfovent C5 Custom Integration for Home Assistant

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![HACS Support](https://img.shields.io/badge/HACS-Custom-orange.svg)

A robust, local-polling Home Assistant custom component to monitor and control **Komfovent** ventilation units equipped with the **C5 Controller** via **Modbus TCP**.

Unlike generic Modbus templates, this integration is purpose-built for the Komfovent C5 memory map. It handles the controller's specific network polling limits, translates standard Home Assistant climate entities into Komfovent preset modes, and dynamically handles unmapped hardware (like missing heaters) without crashing.

## ✨ Features

* **🌡️ Climate Control:** * Turn the AHU On/Off.
    * View and set the target temperature.
    * Change active preset modes (`Comfort 1`, `Comfort 2`, `Economy 1`, `Economy 2`, `Special`, `Program`).
* **📊 Comprehensive Monitoring (Sensors):**
    * **Airflow:** Supply/Extract flows (m³/h), Fan levels (%), and pressures (Pa).
    * **Temperatures:** Supply, Extract, Outdoor, Exhaust, Return Water, and Internal temperatures.
    * **Efficiency:** Thermal efficiency, energy savings, heat exchanger recovery power (W), and Specific Fan Power (SFP).
    * **Maintenance:** Filter impurity levels (%) and active alarm states/codes.
* **🎛️ Feature Switches:**
    * Toggle Override functions, Summer Night Cooling, Operation on Demand, and Recirculation.
    * Enable/Disable Water Heaters, Water Coolers, and Electric Heaters.

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

## 🛠️ Technical Details & Known Behaviors

* **Polling Limits:** The Komfovent C5 network processor is relatively slow. This integration intentionally injects a `300ms` delay between sequential Modbus block reads to prevent overwhelming the controller and causing connection drops.
* **Safe Memory Chunking:** Depending on your specific hardware (e.g., whether you have electric heaters or specific temperature sensors installed), the C5 controller may completely unmap certain Modbus registers. This integration reads memory in small, logical chunks so that a missing hardware feature simply disables that specific entity rather than failing the entire update loop.
* **Zero-Indexing:** The Komfovent Modbus manual uses 1-indexed register addresses, but standard Modbus wire protocols use 0-indexing. This integration handles the `-1` offset automatically under the hood.

## 🐛 Troubleshooting

* **Failed to connect:** Verify that Modbus TCP is enabled on the C5 controller's screen and that your Home Assistant instance is on the same local subnet as the unit.
* **Missing Entities (Unavailable):** If certain switches (like Electric Heater) or sensors are unavailable, it simply means your specific physical machine does not have those features mapped in its firmware. 

---
*Disclaimer: This integration is not officially affiliated with or endorsed by Komfovent. Use at your own risk.*

[![GitHub release](https://img.shields.io/github/release/krozgrov/ha-omlet-integration.svg)](https://github.com/krozgrov/ha-omlet-integration/releases)
[![GitHub stars](https://img.shields.io/github/stars/krozgrov/ha-omlet-integration.svg)](https://github.com/krozgrov/ha-omlet-integration/stargazers)
![GitHub License](https://img.shields.io/github/license/krozgrov/ha-omlet-integration)

# Omlet Smart Chicken Coop Integration for Home Assistant

An integration for Home Assistant that connects your Omlet Smart Coop devices—including the Smart Automatic Chicken Coop Door and Smart Coop Fan—enabling monitoring and control directly from Home Assistant using the official Omlet API.

---

## Sponsor

If you find this integration useful, consider supporting development:

<a href="https://www.buymeacoffee.com/krozgrov" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>

---

## 2026.01.28b5 – Feeder + Restart + Reload Guard

- **Added**: Feeder cover entity for open/close actions.
- **Added**: Feeder sensors for feed level, state, fault, light level, mode, and last open/close timestamps.
- **Added**: `restart_device` service to reboot Omlet devices via the action endpoint.
- **Changed**: Surface a `restart` entry in each device’s actions list when missing.
- **Fixed**: Prevent duplicate entities after integration reloads (all platforms).
- **Fixed**: Reload guard now checks HA StateMachine correctly (fixes platform setup errors).
- **Changed**: Feeder state icon aligned with door-style icon.

## 2026.01.20 – Service Target Mapping

- **Fixed**: Map service device targets using both device serial and deviceId identifiers.

## 2026.01.18 – Stability Fixes

- **Fixed**: Guard against malformed device payloads (non-dict state/config/actions) to avoid coordinator update crashes.
- **Fixed**: Webhook responses now return plain text `ok` for consistent Omlet delivery logs.
- **Fixed**: Webhook token parsing accepts additional auth header schemes/keys to reduce false 401s.

## 2026.01.04 – Translation Alignment

- **Fix**: Restore runtime labels by syncing `translations/en.json` with `strings.json`.

---

# **Smart Door Features**

The Smart Automatic Chicken Coop Door includes:

- Open/close control
- Light control (if your Omlet setup supports it)
- Automatic detection of door state (open, closed, blocked)
- Light & ambient sensor readings
- Battery and Wi-Fi signal monitoring
- Webhook support for real-time state updates

### **Smart Door Screenshots**

| Door Controls | Device Details |
|---|---|
| ![](https://github.com/user-attachments/assets/76ad0dac-3198-4cbc-beb4-4022b8c24e25) | ![](https://github.com/user-attachments/assets/6977606f-8a54-491c-8a00-efdff07e8cff) |

---

# **Smart Fan Features**

The Smart Coop Fan exposes granular configuration and automation entities:

### **Fan Modes**

- **Manual** mode  
- **Time-based** mode (On/Off with per-slot fan speed)
- **Thermostatic** mode (Turn on/off based on temperature thresholds)

### **Entities Provided**

- Ambient temperature & humidity sensors  
- Fan state (on/off), mode, and speed  
- Time schedule entities (S1-1, S1-2, S1-3)  
- Thermostatic threshold & speed entities  
- Boost mode (if supported by your model)  
- Diagnostics entities (temperature, signal strength, battery, etc.)

---

## **Smart Fan Screenshots**

### Control, Configuration, and Diagnostics

| Fan Control & Sensors | Configuration Settings | Diagnostics |
|---|---|---|
| ![](https://github.com/user-attachments/assets/35ff5858-1859-4daa-aa2d-5c5a209cdae7) | ![](https://github.com/user-attachments/assets/caf649ca-f55b-4aa9-b18e-629254209845) | ![](https://github.com/user-attachments/assets/af98d638-3ba0-46fd-bc9d-9d34dbe09c2a) |

### Fan Modes, Actions, and Notifications

| Fan Mode View | Smart Fan Actions | Notifications |
|---|---|---|
| ![](https://github.com/user-attachments/assets/152ffe4e-a795-4f4d-8a99-dc7d64fc0a55) | ![](https://github.com/user-attachments/assets/1cb0983b-49d4-4dc7-be35-e75613e7fee0) | ![](https://github.com/user-attachments/assets/0240aba4-f831-4cf1-a4cf-c2ba295200b7) |

**Note:** This fan is designed to **ventilate** (air movement), not cool like an A/C.

---

# **Smart Feeder Features**

The Smart No Waste Chicken Feeder exposes:

- Open/close control (cover entity)
- Feed level, light level, fault/state, and mode sensors
- Last open/close timestamps

---

# **Installation**

## Prerequisites

1. A working Home Assistant installation.
2. An Omlet account with an API key (generate in Omlet account settings).

---

## Manual Installation

1. Download this repository as a ZIP.
2. Extract into:  
   `custom_components/omlet_smart_coop`
3. Restart Home Assistant.

---

## HACS Installation

1. Open **HACS** → **Integrations**.
2. Click the menu (⋮) → **Custom repositories**.
3. Add:  
   `https://github.com/krozgrov/ha-omlet-integration`  
   Category: **Integration**
4. Search for **Omlet Smart Coop** and install.
5. Restart Home Assistant.

---

# **Configuration**

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Omlet Smart Coop**
3. Enter your API key and polling interval

### Configuration Screenshots

| Initial Setup | Device Discovery |
|---|---|
| ![](https://github.com/user-attachments/assets/739eb66d-94af-430d-bf85-c28ba6825508) | ![](https://github.com/user-attachments/assets/371c9547-eb1d-4569-911a-b65d358fb1b7) |

---

# **API Details**

This integration uses the official [Omlet API](https://smart.omlet.com/developers/api#/).

### Endpoints Used
- `/device` – Retrieve device information  
- `/device/{deviceId}/action/{action}` – Trigger actions  
- `/device/{deviceId}/configuration` – Update device configuration  

---

# **Webhooks (Real-Time Updates)**

To avoid polling delays, enable webhooks:

1. Enable **webhooks** in the integration options  
2. (Optional) Set a `webhook_token`  
3. Integration shows the webhook URL in a notification  
4. Add this URL in the **Omlet Developer Portal → Manage Webhooks**

Modes:

- **Polling + Webhooks (default)**  
- **Webhooks only**: Enable “Disable polling” in options  
- **Polling only**: Disable webhooks

---

# License

MIT License – see [LICENSE](LICENSE) for details.

---

# Support

For issues or feature requests, open an issue:  
https://github.com/krozgrov/ha-omlet-integration/issues

To debug, enable:

```yaml
logger:
  default: warning
  logs:
    custom_components.omlet_smart_coop: debug
```

[![GitHub release](https://img.shields.io/github/release/krozgrov/ha-omlet-integration.svg)](https://github.com/krozgrov/ha-omlet-integration/releases) [![GitHub stars](https://img.shields.io/github/stars/krozgrov/ha-omlet-integration.svg)](https://github.com/krozgrov/ha-omlet-integration/stargazers) ![GitHub License](https://img.shields.io/github/license/krozgrov/ha-omlet-integration)

# Omlet Smart Chicken Coop Integration for Home Assistant

An integration for Home Assistant that connects your Omlet Smart Coop devices—including the Smart Automatic Chicken Coop Door and Smart Coop Fan—enabling monitoring and control directly from Home Assistant using the Omlet official API.

---

## 2025.12.19 - Smart Fan Integration

- **New**: Smart Coop Fan integration with configuration entities for mode, manual speed, time slots, and thermostatic thresholds.
- **Note**: Home Assistant must be **restarted** after updating the integration for entity names/services to refresh in the UI.

---

## Sponsor

A lot of effort is going into this integration. So if you can afford it and want to support me:

<a href="https://www.buymeacoffee.com/krozgrov" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

---

## Features

- **Device Support:** Automatically detects supported Omlet devices including the Smart Automatic Chicken Coop Door and the Smart Chicken Coop Fan.
- **Entity Creation:** Monitor battery, light, Wi-Fi health, fan status, ambient conditions, and configuration settings.
- **Actions:** Trigger door open/close, control lights, fan on/off or Boost mode (when supported).
- **Service Calls:** Door actions, configuration updates, schedules.
- **Webhooks:** Real-time updates without polling delays.

### Screenshots – Core Actions & Device States

| Smart Door Controls | Device Details |
|---|---|
| ![Screenshot 1](https://github.com/user-attachments/assets/76ad0dac-3198-4cbc-beb4-4022b8c24e25) | ![Screenshot 2](https://github.com/user-attachments/assets/6977606f-8a54-491c-8a00-efdff07e8cff) |

---

## Fan Configuration (GUI + Automations)

Fan settings are exposed as Home Assistant entities and compatible with built-in automation services:

- **Mode**: (“Manual”, “Time”, “Thermostatic”)  
- **Manual speed**: (“Low”, “Medium”, “High”)  
- **Time schedule (Slot 1)**: on/off times + speed  
- **Thermostatic thresholds**: temp on/off + speed  

### Screenshots – Fan Settings

| Fan Control / Sensors | Configuration Settings | Diagnostics |
|---|---|---|
| ![Fan Slot 1](https://github.com/user-attachments/assets/35ff5858-1859-4daa-aa2d-5c5a209cdae7) | ![Configuration](https://github.com/user-attachments/assets/caf649ca-f55b-4aa9-b18e-629254209845) | ![Diagnostics](https://github.com/user-attachments/assets/af98d638-3ba0-46fd-bc9d-9d34dbe09c2a) |

| Fan Mode Action | Smart Fan Actions | Notifications |
|---|---|---|
| ![Mode Action](https://github.com/user-attachments/assets/152ffe4e-a795-4f4d-8a99-dc7d64fc0a55) | ![Fan Actions](https://github.com/user-attachments/assets/1cb0983b-49d4-4dc7-be35-e75613e7fee0) | ![Notifications](https://github.com/user-attachments/assets/0240aba4-f831-4cf1-a4cf-c2ba295200b7) |

Note: This fan is designed to **ventilate** (air movement), not cool like an A/C.

---

## Installation

### Prerequisites
1. A working Home Assistant installation.
2. An Omlet account with API access (generate an API key).

### Manual Installation
1. Download the repository as a ZIP.
2. Extract to `custom_components/omlet_smart_coop`.
3. Restart Home Assistant.

### Using HACS
Recommended:
1. HACS → Integrations → Search for **Omlet Smart Coop**.
2. Install latest release and restart Home Assistant.

Alternative (only if needed):
1. Add repository to HACS as Custom Repository.
2. URL: `https://github.com/krozgrov/ha-omlet-integration`, Type: Integration.
3. Install and restart.

---

## Configuration

1. **Settings → Devices & Services → Add Integration**
2. Search **Omlet Integration**
3. Enter API key + polling interval.

### Configuration Screenshots

| Initial Setup | Device Discovery |
|---|---|
| ![Config 1](https://github.com/user-attachments/assets/739eb66d-94af-430d-bf85-c28ba6825508) | ![Config 2](https://github.com/user-attachments/assets/371c9547-eb1d-4569-911a-b65d358fb1b7) |

---

## API Details

This integration uses the [Omlet API](https://smart.omlet.com/developers/api#/).  
Key endpoints:
- `/device` – Retrieve device info
- `/device/{deviceId}/action/{action}` – Trigger actions
- `/device/{deviceId}/configuration` – Update configuration

---

## Webhooks (Real-Time Updates)

Enable webhooks for push-based updates (no polling delay):

- Integration Options → Enable webhooks (optionally set `webhook_token`)
- Integration displays webhook URL in a Home Assistant notification
- Configure webhook in the Omlet Developer Portal
- Choose events (door open/close, light, etc.)

Modes:
- **Legacy polling:** Use interval setting (default)
- **Webhooks only:** Disable polling in Options

---

## License

MIT License – see [LICENSE](LICENSE) for details.

---

## Support

Open an [issue](https://github.com/krozgrov/ha-omlet-integration/issues).  

For bug reports, enable debug logging:

```yaml
logger:
  default: warning
  logs:
    custom_components.omlet_smart_coop: debug

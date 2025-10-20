
# Omlet Smart Automatic Chicken Coop Door Integration for Home Assistant

An integration for Home Assistant that connects your Omlet Smart Automatic Chicken Coop Door and related devices, enabling monitoring and control directly from Home Assistant using the Omlet official API.

## Sponsor

A lot of effort is going into this integration. So if you can afford it and want to support me:

<a href="https://www.buymeacoffee.com/krozgrov" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>


## Features

- **Device Support:** Automatically detects and adds supported Omlet device - Smart Automatic Chicken Coop Door https://www.omlet.us/smart-automatic-chicken-coop-door/.

- **Entity Creation:**
  - Monitor battery levels, Light Levels and other configuration settings.
- **Actions:** Trigger actions such as:
  - Open/close the door.
  - Turn lights on/off.
  <img width="804" alt="Screenshot 2024-12-29 at 3 47 54 PM" src="https://github.com/user-attachments/assets/76ad0dac-3198-4cbc-beb4-4022b8c24e25" />
  <img width="414" alt="Screenshot 2024-12-29 at 4 29 21 PM" src="https://github.com/user-attachments/assets/6977606f-8a54-491c-8a00-efdff07e8cff" />

  - Service Calls to access funcitionality - door open/close, update power settings, and door schedules.
  - Webhooks for real-time updates.

## Installation

### Prerequisites
1. A working Home Assistant installation.
2. An Omlet account with API access (generate an API key from your Omlet account).

### Manual Installation
1. Download the repository as a ZIP file.
2. Extract the contents into the `custom_components/omlet_smart_coop` directory within your Home Assistant configuration folder.
3. Restart Home Assistant.

### Using HACS
- Recommended: Install directly from HACS (no custom repository needed)
  1. In Home Assistant, open HACS → Integrations.
  2. Search for "Omlet Smart Coop" and select it.
  3. Install the latest release and restart Home Assistant when prompted.

- Alternative (only if you don’t see it listed):
  1. In HACS, add this repository as a Custom Repository.
  2. URL: https://github.com/krozgrov/ha-omlet-integration, Type: Integration.
  3. Then search for "Omlet Smart Coop", install, and restart.

## Configuration

1. Navigate to **Settings > Devices & Services > Add Integration**.
2. Search for **Omlet Integration**.
3. Enter your API key and polling interval.
<img width="599" alt="Screenshot 2025-01-05 at 8 26 57 AM" src="https://github.com/user-attachments/assets/739eb66d-94af-430d-bf85-c28ba6825508" />

4. Devices will be automatically discovered and added.
<img width="794" alt="Screenshot 2024-12-29 at 4 28 36 PM" src="https://github.com/user-attachments/assets/371c9547-eb1d-4569-911a-b65d358fb1b7" />

## API Details

This integration uses the [Omlet API](https://smart.omlet.com/developers/api#/). It fetches device states, performs actions, and listens for updates.

Key API endpoints used:
- `/device` - Retrieve device information.
- `/device/{deviceId}/action/{action}` - Trigger device actions.
- `/device/{deviceId}/configuration` - Trigger updates

## Webhooks (Real‑Time Updates)

You can enable real‑time updates using Omlet webhooks so Home Assistant receives state changes immediately (no need to wait for polling).

Steps:
- Ensure your Home Assistant instance is reachable from the internet (Home Assistant Cloud or a configured external URL).
- In the integration Options, enable “Enable webhooks” and (optionally) set a `webhook_token` for verification.
- When enabled, the integration registers a random webhook endpoint and shows the full URL in a Home Assistant notification. You can also call the service `omlet_smart_coop.show_webhook_url` to display it again.
- In the Omlet Developer Portal, visit “Manage Webhooks” and create a webhook pointing to your HA’s public URL shown by the integration.
  - If you set a `webhook_token` in the integration, enter the same token in the portal so the integration can validate incoming requests.
  - Select the events you want to receive (e.g., door opened/closed, light state changes).

Notes:
- When Home Assistant receives a webhook, the integration immediately refreshes device state via the Omlet API to ensure entities reflect the latest values.
- You can choose between legacy polling and webhooks-only mode:
  - Legacy polling: leave "Disable polling" turned OFF (default) and set your preferred polling interval.
  - Webhooks only: turn ON "Disable polling" in Options to stop periodic polling and rely on push updates.
  - If you disable webhooks in Options, the integration unregisters its local webhook handler and falls back to polling.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, feel free to:
- Open an [issue](https://github.com/krozgrov/ha-omlet-integration/issues).

For bug reports, include the debug log, which can be enabled in configuration YAML + restart:

```YAML
logger:
  default: warning
  logs:
    custom_components.omlet_smart_coop: debug

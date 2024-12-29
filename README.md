
# Omlet Smart Automatic Chicken Coop Door - Home Assistant Integration

A **custom integration for Home Assistant** that connects your Omlet Smart Automatic Chicken Coop Door and related devices, enabling monitoring and control directly from Home Assistant using the Omlet Offical API.

## Sponsor

A lot of effort is going into that integration. So if you can afford it and want to support me:

<a href="https://www.buymeacoffee.com/krozgrov" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>


## Features

- **Device Support:** Automatically detects and adds supported Omlet device - Smart Automatic Chicken Coop Door https://www.omlet.us/smart-automatic-chicken-coop-door/.

- **Entity Creation:**
  - Monitor battery levels, Light Levels and other configuration settings.
- **Actions:** Trigger actions such as:
  - Open/close the door.
  - Turn lights on/off.
  <img width="804" alt="Screenshot 2024-12-29 at 3 47 54 PM" src="https://github.com/user-attachments/assets/76ad0dac-3198-4cbc-beb4-4022b8c24e25" />

## Installation

### Prerequisites
1. A working Home Assistant installation.
2. An Omlet account with API access (generate an API key from your Omlet account).

### Manual Installation
1. Download the repository as a ZIP file.
2. Extract the contents into the `custom_components/omlet` directory within your Home Assistant configuration folder.
3. Restart Home Assistant.

### Using HACS - In-progress
1. Add this repository as a custom repository in HACS.
2. Search for **Omlet Integration** and install it.
3. Restart Home Assistant.

## Configuration

1. Navigate to **Settings > Devices & Services > Add Integration**.
2. Search for **Omlet Integration**.
3. Enter your API key.
4. Devices will be automatically discovered and added.

## API Details

This integration uses the [Omlet API](https://smart.omlet.com/developers/api#/). It fetches device states, performs actions, and listens for updates.

Key API endpoints used:
- `/device` - Retrieve device information.
- `/device/{id}/action/{action}` - Trigger device actions.

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
    custom_components.omlet: debug


# Omlet Home Assistant Integration

A **custom integration for Home Assistant** that connects your Omlet Smart Coop and related devices, enabling monitoring and control directly from Home Assistant using the Omlet [Python SDK] (https://smart.omlet.com/developers/python-sdk).

## Features

- **Device Support:** Automatically detect and add supported Omlet devices like the Autodoor.
- **Entity Creation:**
  - Monitor battery levels, Wi-Fi signal strength, and device uptime.
  - Control and monitor the door state (`open`, `closed`) and light state (`on`, `off`).
- **Actions:** Trigger actions such as:
  - Open/close the door.
  - Turn lights on/off.
  - Perform device restarts and firmware updates.
- **Real-Time Updates:**
  - Optional webhook support for live state updates.
  - Configurable polling intervals to conserve battery life.

## Installation

### Prerequisites
1. A working Home Assistant installation.
2. An Omlet account with API access (generate an API key from your Omlet account).

### Manual Installation
1. Download the repository as a ZIP file.
2. Extract the contents into the `custom_components/omlet_integration` directory within your Home Assistant configuration folder.
3. Restart Home Assistant.

### Using HACS
1. Add this repository as a custom repository in HACS.
2. Search for **Omlet Integration** and install it.
3. Restart Home Assistant.

## Configuration

1. Navigate to **Settings > Devices & Services > Add Integration**.
2. Search for **Omlet Integration**.
3. Enter your API key.
4. Devices will be automatically discovered and added.

### Supported Platforms
- **Sensors:**
  - Battery level
  - Wi-Fi signal strength
  - Door state
  - Light state
- **Switches:**
  - Door control (open/close)
  - Light control (on/off)

### Advanced Configuration
You can configure polling intervals, time zones, and sleep settings directly in the device settings.

## Example Entities

| Entity ID                     | Description            | Example State |
|-------------------------------|------------------------|---------------|
| `sensor.autodoor_battery`     | Battery level          | `89%`         |
| `sensor.autodoor_wifi`        | Wi-Fi signal strength  | `-67 dBm`     |
| `switch.autodoor_door`        | Door control           | `open/closed` |
| `switch.autodoor_light`       | Light control          | `on/off`      |

## API Details

This integration uses the [Omlet API](https://smart.omlet.com/developers/api#/). It fetches device states, performs actions, and listens for updates.

Key API endpoints used:
- `/device` - Retrieve device information.
- `/device/{id}/action/{action}` - Trigger device actions.

## Known Issues

- Webhook support is planned for a future update.
- Some devices may have limited functionality depending on the Omlet API.

## Contribution

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m 'Add feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, feel free to:
- Open an [issue](https://github.com/krozgrov/ha-omlet-integration/issues).
- Join the Home Assistant community for support.

## Future Enhancements

- Webhook integration for real-time updates.
- Additional device types and actions.
- Enhanced diagnostics and error handling.

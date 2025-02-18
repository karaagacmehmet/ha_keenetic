# Keenetic Router Integration for Home Assistant
[Russian ver.](README_RU.md)

This is a Home Assistant custom integration for Keenetic Routers. It provides detailed information about your Keenetic router including WiFi networks, ethernet ports, and mesh network status.

## Features

- Monitor router system information (CPU, memory, uptime)
- Control WiFi networks (enable/disable)
- View ethernet port status and statistics
- Monitor mesh network nodes
- View detailed interface statistics

## Installation

### HACS (Recommended)

1. Open HACS
2. Click on "Integrations"
3. Click the "+" button
4. Search for "Keenetic Router"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `ha_keenetic` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Configuration > Integrations
2. Click the "+" button
3. Search for "Keenetic Router"
4. Enter your router's:
   - IP address (default: 192.168.1.1)
   - Port (default: 81)
   - Username (default: admin)
   - Password

## Supported Devices

This integration has been tested with:
- Keenetic Giga
- Keenetic Hero 4g
- Keenetic Sprinter SE

Other Keenetic models should work as well.

## Available Entities

### Sensors
- System Information (CPU, Memory, Uptime)
- WiFi Networks Status
- Ethernet Ports Status
- Mesh Nodes Status

### Switches
- WiFi Networks (Enable/Disable)

## Contributing

Feel free to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

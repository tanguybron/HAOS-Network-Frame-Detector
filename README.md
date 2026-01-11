# Network Frame Detector

A secure, Home Assistant OS-compatible custom integration for detecting specific network frames to trigger automations.

## ⚠️ Security-First Design

This integration is designed with security as the primary concern. It **does not** act as a packet sniffer or network interception tool. It provides a safe, limited mechanism for detecting specific network patterns on configured ports.

## Features

- **Secure by Design**: No raw sockets, no promiscuous mode, no packet injection
- **Pattern Matching**: Support for string, regex, and hex pattern matching
- **Protocol Support**: UDP and TCP
- **Multicast Support**: Optional multicast group membership for mDNS discovery
- **Cooldown Protection**: Configurable cooldown period to prevent spam
- **Event Firing**: Fires Home Assistant events on detection
- **Binary Sensor**: Provides a binary sensor that turns ON when frames are detected

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu (⋮) → "Custom repositories"
4. Add this repository URL: `https://github.com/USERNAME/HAOS-Network-Frame-Detector` (replace USERNAME with your GitHub username)
5. Select category: **Integration**
6. Click "Add"
7. Search for "Network Frame Detector" and install
8. Restart Home Assistant
9. Add the integration via Settings → Devices & Services → Add Integration

### Manual Installation

1. Copy the `custom_components/network_frame_detector` folder to your Home Assistant `custom_components` directory
   - Via SSH: `/config/custom_components/network_frame_detector/`
   - Via Samba: `\\<haos-ip>\config\custom_components\network_frame_detector\`
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services → Add Integration

> **Note**: See [PUBLISHING.md](PUBLISHING.md) for detailed installation instructions.

## Configuration

Configuration is done entirely through the Home Assistant UI (Config Flow).

### Configuration Parameters

- **Name**: Unique name for this detection rule (1-64 characters)
- **Protocol**: UDP or TCP
- **Port**: Port number to listen on (1-65535)
- **Multicast**: Enable multicast support (for mDNS, etc.)
- **Pattern Type**: 
  - `string`: Simple string matching (UTF-8 encoded)
  - `regex`: Regular expression matching (pre-compiled for safety)
  - `hex`: Hexadecimal byte pattern matching
- **Pattern Value**: The pattern to match against packet payloads
- **Cooldown**: Minimum seconds between detections (0-3600)
- **Sensor Duration**: How long the sensor stays ON after detection (1-3600 seconds)
- **Source IP Filter** (optional): Only match packets from this specific IP address

## Example: Google Cast mDNS Detection

To detect when a Google Cast device announces itself via mDNS:

1. Add the integration via Config Flow
2. Configure:
   - **Name**: `Google Cast Discovery`
   - **Protocol**: `UDP`
   - **Port**: `5353` (mDNS port)
   - **Multicast**: `true`
   - **Pattern Type**: `string`
   - **Pattern Value**: `_googlecast._tcp.local`
   - **Cooldown**: `5` seconds
   - **Sensor Duration**: `30` seconds
   - **Source IP Filter**: (leave empty)

3. The binary sensor will turn ON when a Google Cast device is discovered
4. An event `network_frame_detected` will be fired with detection details

### Automation Example

```yaml
automation:
  - alias: "Google Cast Device Detected"
    trigger:
      - platform: event
        event_type: network_frame_detected
        event_data:
          entry_id: <your_entry_id>
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "A Google Cast device was detected on the network!"
```

## Security Model

### What This Integration Does

- Binds to a **specific, user-configured port** (no promiscuous mode)
- Listens for incoming packets on that port only
- Matches packet payloads against user-configured patterns
- Fires Home Assistant events and updates binary sensor state
- **Never stores packet data** beyond in-memory pattern matching
- **Never forwards or modifies** network traffic
- **Never captures credentials** or sensitive data
- **Never identifies devices** by MAC address
- **Never fingerprints clients**

### Security Guarantees

1. **No Raw Sockets**: Uses standard Python socket API with proper binding
2. **No Promiscuous Mode**: Only receives packets destined for the configured port
3. **No Packet Injection**: Read-only operation, never sends packets
4. **No Packet Modification**: Never modifies network traffic
5. **No Traffic Forwarding**: Never forwards packets to other destinations
6. **No Credential Capture**: Pattern matching only, no payload storage
7. **No External Network Access**: Only listens on local network
8. **No Privilege Escalation**: Uses standard socket permissions
9. **No File Writes**: Only writes Home Assistant state (via standard HA mechanisms)
10. **No Dynamic Code Execution**: All code is static, no eval/exec
11. **ReDoS Protection**: Regex patterns are pre-compiled and validated
12. **Input Validation**: All user inputs are strictly validated with length limits

### Memory Safety

- Maximum pattern length: 1024 bytes
- Maximum payload inspection: 4096 bytes per packet
- Maximum pattern value string: 2048 characters
- Maximum regex pattern length: 256 characters
- Constant memory usage (no packet buffering)
- O(1) per-packet processing

### Time Safety

- Pattern matching is time-bounded
- TCP connections have 1-second timeout
- No busy loops or blocking operations
- All operations are async

## Threat Model

### Assumptions

1. **Trusted Local Network**: This integration assumes the local network is trusted. It does not protect against malicious actors on the network.
2. **Home Assistant Security**: Relies on Home Assistant's security model for access control.
3. **No Network Isolation**: Does not provide network isolation or firewall capabilities.
4. **Port Availability**: Assumes the configured port is available and not in use by other services.

### What This Integration Protects Against

- **Accidental Misuse**: Strict input validation prevents configuration errors
- **Resource Exhaustion**: Memory and time limits prevent DoS attacks via malformed packets
- **ReDoS Attacks**: Regex patterns are validated and pre-compiled
- **Data Exfiltration**: No packet data is stored or transmitted outside Home Assistant

### What This Integration Does NOT Protect Against

- **Network Eavesdropping**: This integration itself does not prevent network eavesdropping (that's a network-level concern)
- **Malicious Network Traffic**: Does not filter or block malicious traffic
- **Port Conflicts**: Does not prevent other services from using the same port
- **Privilege Escalation**: Does not provide additional security beyond Home Assistant's model

## Non-Goals

This integration explicitly **does not**:

- Act as a network security tool
- Provide network monitoring or analysis
- Capture or store network traffic
- Identify devices by MAC address
- Fingerprint network clients
- Provide intrusion detection
- Act as a firewall or network filter
- Support packet injection or modification
- Support traffic forwarding or proxying
- Provide network diagnostics or troubleshooting tools
- Support promiscuous mode or raw socket access

## Architecture

```
┌─────────────────────────────────────────┐
│  Home Assistant                         │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Config Flow (UI)                 │ │
│  └───────────────────────────────────┘ │
│           │                             │
│           ▼                             │
│  ┌───────────────────────────────────┐ │
│  │  Integration Setup                 │ │
│  └───────────────────────────────────┘ │
│           │                             │
│           ├─────────────────────────────┤
│           │                             │
│           ▼                             │
│  ┌───────────────────────────────────┐ │
│  │  SecureNetworkListener             │ │
│  │  - Binds to port                   │ │
│  │  - Matches patterns                │ │
│  │  - Fires callbacks                 │ │
│  └───────────────────────────────────┘ │
│           │                             │
│           ▼                             │
│  ┌───────────────────────────────────┐ │
│  │  Coordinator                       │ │
│  │  - Manages state                   │ │
│  │  - Fires events                    │ │
│  │  - Handles cooldown                │ │
│  └───────────────────────────────────┘ │
│           │                             │
│           ▼                             │
│  ┌───────────────────────────────────┐ │
│  │  Binary Sensor                     │ │
│  │  - Exposes state                   │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
           │
           ▼
    Network Interface
    (UDP/TCP on port)
```

## Limitations

1. **One Rule Per Entry**: Each configuration entry represents exactly one detection rule
2. **Port Binding**: Only one entry can use a specific port at a time
3. **Pattern Matching Only**: Only matches payload patterns, not headers or metadata
4. **No Packet Analysis**: Does not parse protocol headers or provide protocol-specific features
5. **Local Network Only**: Only works on the local network interface

## Troubleshooting

### Port Already in Use

If you see "Port is already in use", another entry is using that port. Each port can only be used by one detection rule.

### No Detections

1. Verify the pattern matches the actual packet payload
2. Check that the port is correct
3. Ensure multicast is enabled if listening for mDNS traffic
4. Verify the protocol (UDP vs TCP) matches the traffic
5. Check Home Assistant logs for errors

### Pattern Not Matching

- For string patterns: Ensure exact byte match (case-sensitive)
- For regex patterns: Test your regex pattern separately first
- For hex patterns: Ensure even number of hex characters, no spaces/colons

## Development

### Code Structure

- `__init__.py`: Integration setup and entry point
- `config_flow.py`: Configuration UI and validation
- `const.py`: Constants and security limits
- `listener.py`: Secure network listener implementation
- `coordinator.py`: State management and event coordination
- `binary_sensor.py`: Binary sensor platform implementation

### Security Review Checklist

- [x] No raw sockets
- [x] No promiscuous mode
- [x] No packet injection
- [x] No packet modification
- [x] No traffic forwarding
- [x] No credential capture
- [x] No payload storage
- [x] No external network access
- [x] No privilege escalation
- [x] No file writes (except HA state)
- [x] No dynamic code execution
- [x] ReDoS protection
- [x] Input validation
- [x] Memory limits
- [x] Time limits

## License

This integration is provided as-is for use with Home Assistant. See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure all security constraints are maintained and include tests for new features.

## Support

For issues, feature requests, or security concerns, please open an issue on GitHub.

## Disclaimer

This integration is designed for legitimate network frame detection in trusted Home Assistant environments. Users are responsible for ensuring compliance with local laws and network policies. The authors are not responsible for misuse of this software.


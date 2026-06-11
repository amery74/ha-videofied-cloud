# Videofied Cloud for Home Assistant

Custom Home Assistant integration for Videofied / RSI Connected Home cloud alarm systems.

## Features

Current V1:

- Login with email and password
- Automatic token generation
- Read alarm panel state from Videofied Cloud
- Read panel connection status
- Read devices, battery, status and temperature
- Read latest image event from the event history
- Download latest received picture
- Button to request a new picture from streaming detectors

Planned V2:

- Arm / disarm support
- Better camera handling
- HACS default repository support

## Installation

Copy the folder:

```text
custom_components/videofied_cloud
```

to:

```text
/config/custom_components/videofied_cloud
```

Restart Home Assistant, then add the integration from:

```text
Settings → Devices & services → Add integration → Videofied Cloud
```

## Disclaimer

This project is community-made and is not affiliated with Videofied, RSI, Resideo, or TSP Sécurité.

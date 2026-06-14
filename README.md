# ha-videofied-cloud

Home Assistant custom integration for Videofied / RSI Cloud alarm systems.

## Current status

Experimental V0.1.1.

Features:

- Login with email and password.
- Automatic token generation.
- Read-only alarm state.
- Device sensors for battery/status/temperature.
- Last image camera from event history.
- Buttons to request a picture from camera detectors.

Not implemented yet:

- Arm / disarm commands.

## Installation via HACS custom repository

1. HACS → Integrations → Custom repositories.
2. Add: `https://github.com/amery74/ha-videofied-cloud`
3. Category: Integration.
4. Download **Videofied Cloud**.
5. Restart Home Assistant.
6. Settings → Devices & services → Add integration → **Videofied Cloud**.

## Warning

This is an unofficial integration based on observed Videofied Cloud API behavior.
Use at your own risk and do not rely on it as the only alarm notification path.

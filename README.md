# ha-videofied-cloud

Home Assistant custom integration for Videofied Cloud / RSI / TSP alarm systems.

## Status

Experimental integration generated from observed Videofied Cloud traffic.

### v0.1.5

- Fixes backend variants using `app3-a2`.
- Uses the authenticated panel host dynamically.
- Supports GET-first fallback for `getpanelinfo` and `getEventsList`.
- Keeps POST for `takePicture`.
- Keeps automatic email/password authentication.

## Features

- Email/password login.
- Automatic token generation.
- Read-only alarm state.
- Device battery/status/temperature sensors.
- Last event sensor.
- Camera entities for latest received images.
- Buttons to request detector pictures.

## Installation

Copy `custom_components/videofied_cloud` to your Home Assistant `/config/custom_components/` folder, or add this repository to HACS as a custom integration.

Restart Home Assistant, then add **Videofied Cloud** from Settings → Devices & services.

## Warning

This is unofficial and not affiliated with Videofied, RSI, or TSP. Use at your own risk.


## Changelog

### 0.1.5
- Fix boolean query parameters for Home Assistant/aiohttp GET requests.


## v0.1.5

- Handle `TAKE_PICTURE_ERROR` as a friendly Home Assistant service error.
- Avoid camera stream tracebacks when an image URL is expired or rejected.
- Try direct image download before the Videofied proxy endpoint.


## v0.1.5

- Adds a 25 second wait after `takePicture` before refreshing events and downloading the new MotionViewer image.
- This matches the observed delay in the official Videofied app.

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import VideofiedApiError, VideofiedCloudApi
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, PICTURE_DELAY_SECONDS

_LOGGER = logging.getLogger(__name__)


class VideofiedDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Videofied Cloud data."""

    def __init__(self, hass: HomeAssistant, api: VideofiedCloudApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.last_picture: dict[str, bytes] = {}
        self.last_picture_event: dict[str, dict[str, Any]] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        info = await self.api.get_panel_info()
        events = await self.api.get_events_list(offset=0, media_only=False)
        return {"panel_info": info, "events": events}

    async def async_take_picture(self, camera_index: str | int) -> None:
        """Request a new picture and wait for the panel/cloud to publish it.

        Videofied MotionViewer pictures are not available immediately after
        takePicture returns picture_status=0. The official app typically sees
        the new PictureReceived event about 25 seconds later.
        """
        result = await self.api.take_picture(camera_index)
        if isinstance(result, dict) and result.get("picture_status") not in (0, "0", None):
            raise VideofiedApiError(f"Unexpected picture response: {result}")
        await asyncio.sleep(PICTURE_DELAY_SECONDS)
        await self.async_request_refresh()
        await self.async_update_picture(camera_index)

    async def async_update_picture(self, camera_index: str | int) -> bytes | None:
        key = str(camera_index)
        event = await self.api.get_latest_picture_event(camera_index)
        if not event:
            return self.last_picture.get(key)
        try:
            image = await self.api.download_picture_from_event(event)
        except VideofiedApiError as err:
            _LOGGER.warning("Unable to download Videofied picture for camera %s: %s", camera_index, err)
            return self.last_picture.get(key)
        if image:
            self.last_picture[key] = image
            self.last_picture_event[key] = event
            return image
        return self.last_picture.get(key)

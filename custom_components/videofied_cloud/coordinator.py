from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

from .api import VideofiedCloudApi, VideofiedCloudApiError
from .const import DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN


class VideofiedDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: VideofiedCloudApi) -> None:
        super().__init__(
            hass,
            hass.logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.get_panel_info()
        except VideofiedCloudApiError as err:
            raise UpdateFailed(str(err)) from err

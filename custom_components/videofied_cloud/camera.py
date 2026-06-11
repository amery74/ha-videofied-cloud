from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VideofiedDataCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VideofiedDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[Camera] = []
    for dev_id, device in coordinator.data.get("data", {}).get("devices", {}).items():
        if device.get("type") == "Streaming":
            entities.append(VideofiedCamera(coordinator, entry.entry_id, dev_id, device.get("name", dev_id)))
    async_add_entities(entities)


class VideofiedCamera(CoordinatorEntity[VideofiedDataCoordinator], Camera):
    def __init__(self, coordinator: VideofiedDataCoordinator, entry_id: str, camera_id: str, camera_name: str) -> None:
        Camera.__init__(self)
        CoordinatorEntity.__init__(self, coordinator)
        self.camera_id = camera_id
        self._attr_unique_id = f"{entry_id}_camera_{camera_id}"
        self._attr_name = f"Videofied {camera_name}"
        self._last_image: bytes | None = None

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        event = await self.coordinator.api.get_latest_picture_event(self.camera_id)
        if not event:
            return self._last_image
        self._last_image = await self.coordinator.api.download_picture(event["PictureURI"], event["PictureToken"])
        return self._last_image

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
    devices = _panel_data(coordinator).get("devices", {})
    entities = []
    for dev_id, dev in devices.items():
        if dev.get("type") == "Streaming":
            entities.append(VideofiedCamera(coordinator, entry.entry_id, dev_id, dev.get("name") or f"Camera {dev_id}"))
    async_add_entities(entities)


def _panel_data(coordinator: VideofiedDataCoordinator) -> dict:
    info = coordinator.data.get("panel_info", {}) if coordinator.data else {}
    return info.get("data", {})


class VideofiedCamera(CoordinatorEntity[VideofiedDataCoordinator], Camera):
    def __init__(self, coordinator: VideofiedDataCoordinator, entry_id: str, camera_id: str, name: str) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self.camera_id = str(camera_id)
        safe_name = name.replace("$", " ").strip()
        self._attr_unique_id = f"{entry_id}_camera_{camera_id}"
        self._attr_name = f"Videofied {safe_name}"
        self._attr_should_poll = True

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        return await self.coordinator.async_update_picture(self.camera_id)

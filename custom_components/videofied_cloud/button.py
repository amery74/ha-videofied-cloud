from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .api import VideofiedApiError
from .coordinator import VideofiedDataCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VideofiedDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    devices = _panel_data(coordinator).get("devices", {})
    entities = []
    for dev_id, dev in devices.items():
        if dev.get("type") == "Streaming":
            entities.append(VideofiedTakePictureButton(coordinator, entry.entry_id, dev_id, dev.get("name") or f"Camera {dev_id}"))
    async_add_entities(entities)


def _panel_data(coordinator: VideofiedDataCoordinator) -> dict:
    info = coordinator.data.get("panel_info", {}) if coordinator.data else {}
    return info.get("data", {})


class VideofiedTakePictureButton(CoordinatorEntity[VideofiedDataCoordinator], ButtonEntity):
    def __init__(self, coordinator: VideofiedDataCoordinator, entry_id: str, camera_id: str, name: str) -> None:
        super().__init__(coordinator)
        self.camera_id = str(camera_id)
        safe_name = name.replace("$", " ").strip()
        self._attr_unique_id = f"{entry_id}_take_picture_{camera_id}"
        self._attr_name = f"Videofied {safe_name} Take Picture"

    async def async_press(self) -> None:
        try:
            await self.coordinator.async_take_picture(self.camera_id)
        except VideofiedApiError as err:
            message = str(err)
            if "TAKE_PICTURE_ERROR" in message:
                raise HomeAssistantError(
                    "Videofied refused the picture request. The detector may be unavailable, asleep, or a picture request may have been made too recently."
                ) from err
            raise HomeAssistantError(f"Videofied picture request failed: {message}") from err

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VideofiedDataCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VideofiedDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []
    for dev_id, device in coordinator.data.get("data", {}).get("devices", {}).items():
        if device.get("type") == "Streaming":
            entities.append(VideofiedTakePictureButton(coordinator, entry.entry_id, dev_id, device.get("name", dev_id)))
    async_add_entities(entities)


class VideofiedTakePictureButton(CoordinatorEntity[VideofiedDataCoordinator], ButtonEntity):
    def __init__(self, coordinator: VideofiedDataCoordinator, entry_id: str, camera_id: str, camera_name: str) -> None:
        super().__init__(coordinator)
        self.camera_id = camera_id
        self._attr_unique_id = f"{entry_id}_camera_{camera_id}_take_picture"
        self._attr_name = f"Videofied {camera_name} Take Picture"

    async def async_press(self) -> None:
        await self.coordinator.api.take_picture(self.camera_id)
        await self.coordinator.async_request_refresh()

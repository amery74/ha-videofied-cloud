from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VideofiedDataCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VideofiedDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        VideofiedSimpleSensor(coordinator, entry.entry_id, "connection", "Connection"),
        VideofiedSimpleSensor(coordinator, entry.entry_id, "last_event", "Last Event"),
    ]

    devices = _panel_data(coordinator).get("devices", {})
    for dev_id, dev in devices.items():
        name = dev.get("name") or f"Device {dev_id}"
        entities.append(VideofiedDeviceSensor(coordinator, entry.entry_id, dev_id, name, "battery"))
        entities.append(VideofiedDeviceSensor(coordinator, entry.entry_id, dev_id, name, "status"))
        entities.append(VideofiedDeviceSensor(coordinator, entry.entry_id, dev_id, name, "temperature"))

    async_add_entities(entities)


def _panel_data(coordinator: VideofiedDataCoordinator) -> dict:
    info = coordinator.data.get("panel_info", {}) if coordinator.data else {}
    return info.get("data", {})


class VideofiedSimpleSensor(CoordinatorEntity[VideofiedDataCoordinator], SensorEntity):
    def __init__(self, coordinator: VideofiedDataCoordinator, entry_id: str, key: str, name: str) -> None:
        super().__init__(coordinator)
        self.key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = f"Videofied {name}"

    @property
    def native_value(self):
        if self.key == "connection":
            return _panel_data(self.coordinator).get("connection")
        if self.key == "last_event":
            events = self.coordinator.data.get("events", []) if self.coordinator.data else []
            if events:
                return events[0].get("Event") or events[0].get("Name")
        return None


class VideofiedDeviceSensor(CoordinatorEntity[VideofiedDataCoordinator], SensorEntity):
    def __init__(self, coordinator: VideofiedDataCoordinator, entry_id: str, dev_id: str, dev_name: str, field: str) -> None:
        super().__init__(coordinator)
        self.dev_id = str(dev_id)
        self.field = field
        safe_name = dev_name.replace("$", " ").strip()
        self._attr_unique_id = f"{entry_id}_device_{dev_id}_{field}"
        self._attr_name = f"Videofied {safe_name} {field.title()}"

    @property
    def native_value(self):
        device = _panel_data(self.coordinator).get("devices", {}).get(self.dev_id, {})
        return device.get(self.field)

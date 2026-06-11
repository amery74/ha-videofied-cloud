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
        VideofiedConnectionSensor(coordinator, entry.entry_id),
        VideofiedZoneStatusSensor(coordinator, entry.entry_id),
    ]
    devices = coordinator.data.get("data", {}).get("devices", {})
    for dev_id, device in devices.items():
        entities.append(VideofiedDeviceBatterySensor(coordinator, entry.entry_id, dev_id, device.get("name", dev_id)))
        entities.append(VideofiedDeviceStatusSensor(coordinator, entry.entry_id, dev_id, device.get("name", dev_id)))
        entities.append(VideofiedDeviceTemperatureSensor(coordinator, entry.entry_id, dev_id, device.get("name", dev_id)))
    async_add_entities(entities)


class VideofiedBaseSensor(CoordinatorEntity[VideofiedDataCoordinator], SensorEntity):
    def __init__(self, coordinator: VideofiedDataCoordinator, unique_id: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_name = name


class VideofiedConnectionSensor(VideofiedBaseSensor):
    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, f"{entry_id}_connection", "Videofied Connection")

    @property
    def native_value(self):
        return self.coordinator.data.get("data", {}).get("connection")


class VideofiedZoneStatusSensor(VideofiedBaseSensor):
    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, f"{entry_id}_zone_1_status", "Videofied Zone 1 Status")

    @property
    def native_value(self):
        return self.coordinator.data.get("data", {}).get("zones", {}).get("Zone 1", {}).get("realstatus")


class VideofiedDeviceBatterySensor(VideofiedBaseSensor):
    def __init__(self, coordinator, entry_id, dev_id, dev_name):
        super().__init__(coordinator, f"{entry_id}_device_{dev_id}_battery", f"Videofied {dev_name} Battery")
        self.dev_id = dev_id

    @property
    def native_value(self):
        return self.coordinator.data.get("data", {}).get("devices", {}).get(self.dev_id, {}).get("battery")


class VideofiedDeviceStatusSensor(VideofiedBaseSensor):
    def __init__(self, coordinator, entry_id, dev_id, dev_name):
        super().__init__(coordinator, f"{entry_id}_device_{dev_id}_status", f"Videofied {dev_name} Status")
        self.dev_id = dev_id

    @property
    def native_value(self):
        return self.coordinator.data.get("data", {}).get("devices", {}).get(self.dev_id, {}).get("status")


class VideofiedDeviceTemperatureSensor(VideofiedBaseSensor):
    def __init__(self, coordinator, entry_id, dev_id, dev_name):
        super().__init__(coordinator, f"{entry_id}_device_{dev_id}_temperature", f"Videofied {dev_name} Temperature")
        self.dev_id = dev_id
        self._attr_native_unit_of_measurement = "°C"

    @property
    def native_value(self):
        value = self.coordinator.data.get("data", {}).get("devices", {}).get(self.dev_id, {}).get("temperature")
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

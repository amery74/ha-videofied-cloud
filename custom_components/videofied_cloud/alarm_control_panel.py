from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VideofiedDataCoordinator

STATE_MAP = {
    "Disarm": AlarmControlPanelState.DISARMED,
    "Normal": AlarmControlPanelState.ARMED_AWAY,
    "External": AlarmControlPanelState.ARMED_HOME,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VideofiedDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VideofiedAlarmPanel(coordinator, entry.entry_id)])


class VideofiedAlarmPanel(CoordinatorEntity[VideofiedDataCoordinator], AlarmControlPanelEntity):
    _attr_supported_features = AlarmControlPanelEntityFeature(0)

    def __init__(self, coordinator: VideofiedDataCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_alarm"
        self._attr_name = "Videofied Alarm"

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        try:
            status = self.coordinator.data["data"]["zones"]["Zone 1"]["realstatus"]
        except Exception:
            return None
        return STATE_MAP.get(status, AlarmControlPanelState.UNKNOWN)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get("data", {})
        zone = data.get("zones", {}).get("Zone 1", {})
        return {
            "raw_status": zone.get("status"),
            "realstatus": zone.get("realstatus"),
            "lockmode": zone.get("lockmode"),
            "connection": data.get("connection"),
            "serial": data.get("serial"),
        }

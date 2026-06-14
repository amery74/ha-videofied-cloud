from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VideofiedDataCoordinator


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
        state = self._zone.get("realstatus") or self._zone.get("status")
        if state == "Disarm":
            return AlarmControlPanelState.DISARMED
        if state == "Normal":
            return AlarmControlPanelState.ARMED_AWAY
        if state == "External":
            return AlarmControlPanelState.ARMED_HOME
        return None

    @property
    def _zone(self) -> dict:
        info = self.coordinator.data.get("panel_info", {}) if self.coordinator.data else {}
        return info.get("data", {}).get("zones", {}).get("Zone 1", {})

    @property
    def extra_state_attributes(self) -> dict:
        return dict(self._zone)

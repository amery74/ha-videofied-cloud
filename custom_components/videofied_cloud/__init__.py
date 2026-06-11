from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VideofiedCloudApi
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import VideofiedDataCoordinator

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL, Platform.SENSOR, Platform.BUTTON, Platform.CAMERA]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = VideofiedCloudApi(session, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    coordinator = VideofiedDataCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

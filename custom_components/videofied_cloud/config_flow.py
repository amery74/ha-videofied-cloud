from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VideofiedCloudApi, VideofiedCloudApiError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN


class VideofiedCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = VideofiedCloudApi(session, user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
            try:
                await api.authenticate()
            except VideofiedCloudApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(api.panel_serial or user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=api.panel_name or "Videofied Cloud",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

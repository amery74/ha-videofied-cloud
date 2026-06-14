from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VideofiedAuthError, VideofiedCloudApi, VideofiedApiError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)


class VideofiedCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]
            api = VideofiedCloudApi(async_get_clientsession(self.hass), email, password)
            try:
                await api.authenticate()
            except (VideofiedAuthError, VideofiedApiError) as err:
                _LOGGER.warning("Videofied authentication failed: %s", err)
                errors["base"] = "auth"
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Unexpected Videofied error: %s", err)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(email)
                self._abort_if_unique_id_configured()
                title = api.panel.get("name") if api.panel else email
                return self.async_create_entry(
                    title=title or email,
                    data={CONF_EMAIL: email, CONF_PASSWORD: password},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

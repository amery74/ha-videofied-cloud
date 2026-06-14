from __future__ import annotations

import hashlib
import logging
from typing import Any
from urllib.parse import quote

import aiohttp

from .const import APP_VERSION, BASE_URL, CLIENT_CHALLENGE_SEED, PASSWORD_PREFIX

_LOGGER = logging.getLogger(__name__)


class VideofiedAuthError(Exception):
    """Authentication failed."""


class VideofiedApiError(Exception):
    """Videofied API error."""


class VideofiedCloudApi:
    """Small async API client for Videofied Cloud."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self.email = email.strip()
        self.password = password
        self.token: str | None = None
        self.panel: dict[str, Any] | None = None
        self.host: str | None = None

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    @property
    def _client_challenge(self) -> str:
        return self._sha256(CLIENT_CHALLENGE_SEED)

    async def _request(self, method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
        """Send a request to Videofied Cloud.

        The Videofied app family uses a mix of POST JSON and GET query parameters
        depending on the backend host returned after authentication (rsiapp-a1, app3-a2, ...).
        """
        payload = payload or {}
        if method.upper() == "GET":
            # aiohttp/yarl does not accept bool values as query params.
            # The Videofied API expects lowercase JSON-like booleans in GET queries.
            params = {
                key: ("true" if value is True else "false" if value is False else value)
                for key, value in payload.items()
            }
            request = self._session.get(url, params=params, timeout=30)
        else:
            request = self._session.post(url, json=payload, timeout=30)

        async with request as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise VideofiedApiError(f"HTTP {resp.status}: {text[:300]}")
            try:
                return await resp.json(content_type=None)
            except Exception as err:  # noqa: BLE001
                raise VideofiedApiError(f"Invalid JSON response from {url}: {text[:300]}") from err

    async def _post(self, url: str, payload: dict[str, Any]) -> Any:
        return await self._request("POST", url, payload)

    async def _get(self, url: str, payload: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", url, payload or {})

    async def _get_then_post(self, url: str, payload: dict[str, Any]) -> Any:
        """Prefer GET, fallback to POST for older Videofied hosts."""
        try:
            return await self._get(url, payload)
        except VideofiedApiError as get_err:
            _LOGGER.debug("GET failed for %s, falling back to POST: %s", url, get_err)
            return await self._post(url, payload)

    async def authenticate(self) -> None:
        """Authenticate and populate token, panel and host."""
        challenge_data = await self._post(
            f"{BASE_URL}/rsiapp/node-login/authentication/GetServerChallenge",
            {"login": self.email},
        )
        challenge = challenge_data.get("challenge")
        if not challenge:
            raise VideofiedAuthError("Missing server challenge")

        # Observed fallback used by current Videofied/TSP app when GetSalt returns 404.
        stored_password = self._sha256(PASSWORD_PREFIX + self.password)
        auth_password = self._sha256(
            challenge + self._client_challenge + self.email + stored_password
        )

        auth = await self._post(
            f"{BASE_URL}/rsiapp/node-login/authentication/Authenticate",
            {
                "login": self.email,
                "password": auth_password,
                "clientChallenge": self._client_challenge,
                "version": APP_VERSION,
            },
        )

        if "token" not in auth:
            raise VideofiedAuthError(f"Authentication failed: {auth}")

        self.token = auth["token"]
        panels = auth.get("user", {}).get("panels", [])
        if not panels:
            raise VideofiedAuthError("No panel returned by Videofied Cloud")
        self.panel = panels[0]
        self.host = self.panel.get("ecosystem", {}).get("host")
        if not self.host:
            raise VideofiedAuthError("Missing panel host")

    async def ensure_authenticated(self) -> None:
        if not self.token or not self.host:
            await self.authenticate()

    async def get_panel_info(self) -> dict[str, Any]:
        await self.ensure_authenticated()
        assert self.host and self.token
        try:
            return await self._get_then_post(f"{self.host}/node-app/getpanelinfo", {"token": self.token})
        except VideofiedApiError:
            # Token may be expired. Authenticate once and retry.
            _LOGGER.debug("Panel info failed; re-authenticating")
            await self.authenticate()
            assert self.host and self.token
            return await self._get_then_post(f"{self.host}/node-app/getpanelinfo", {"token": self.token})

    async def get_events_list(self, offset: int = 0, media_only: bool = False) -> list[dict[str, Any]]:
        await self.ensure_authenticated()
        assert self.host and self.token
        data = await self._get_then_post(
            f"{self.host}/node-app/getEventsList",
            {"token": self.token, "offset": offset, "mediaOnly": media_only},
        )
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("data", []) or data.get("events", []) or []
        return []

    async def take_picture(self, camera_index: str | int) -> dict[str, Any]:
        await self.ensure_authenticated()
        assert self.host and self.token
        return await self._post(
            f"{self.host}/node-app/takePicture",
            {"token": self.token, "camera_index": str(camera_index)},
        )

    async def get_latest_picture_event(self, camera_index: str | int | None = None) -> dict[str, Any] | None:
        events = await self.get_events_list(offset=0, media_only=False)
        wanted = str(camera_index) if camera_index is not None else None
        for event in events:
            if event.get("Event") != "PictureReceived":
                continue
            if wanted is not None and str(event.get("Camera")) != wanted:
                continue
            if event.get("PictureURI") and event.get("PictureToken"):
                return event
        return None

    async def download_picture_from_event(self, event: dict[str, Any]) -> bytes | None:
        await self.ensure_authenticated()
        assert self.host
        uri = event.get("PictureURI")
        pic_token = event.get("PictureToken")
        if not uri or not pic_token:
            return None
        proxy_url = f"{self.host}/node-app/proxy?uri=" + quote(
            f"{uri}?authenticationbearer={pic_token}", safe=""
        )
        async with self._session.get(proxy_url, timeout=30) as resp:
            if resp.status >= 400:
                raise VideofiedApiError(f"Image HTTP {resp.status}")
            return await resp.read()

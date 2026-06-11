from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import quote

import aiohttp

from .const import APP_VERSION, BASE_URL, CLIENT_CHALLENGE_SEED, LEGACY_PASSWORD_SEED


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class VideofiedCloudApiError(Exception):
    """Videofied Cloud API error."""


class VideofiedCloudApi:
    """Small async API client for Videofied Cloud."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None
        self._host: str | None = None
        self._panel_serial: str | None = None
        self._panel_name: str | None = None

    @property
    def panel_name(self) -> str | None:
        return self._panel_name

    @property
    def panel_serial(self) -> str | None:
        return self._panel_serial

    @property
    def host(self) -> str:
        if not self._host:
            raise VideofiedCloudApiError("Not authenticated")
        return self._host

    async def _post_json(self, url: str, payload: dict[str, Any]) -> Any:
        async with self._session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise VideofiedCloudApiError(f"HTTP {resp.status}: {text}")
            try:
                return await resp.json(content_type=None)
            except Exception as err:
                raise VideofiedCloudApiError(f"Invalid JSON response: {text}") from err

    async def authenticate(self) -> None:
        challenge_data = await self._post_json(
            f"{BASE_URL}/rsiapp/node-login/authentication/GetServerChallenge",
            {"login": self._email},
        )
        challenge = challenge_data["challenge"]

        client_challenge = _sha256(CLIENT_CHALLENGE_SEED)
        stored_password = _sha256(LEGACY_PASSWORD_SEED + self._password)
        auth_password = _sha256(challenge + client_challenge + self._email + stored_password)

        auth_data = await self._post_json(
            f"{BASE_URL}/rsiapp/node-login/authentication/Authenticate",
            {
                "login": self._email,
                "password": auth_password,
                "clientChallenge": client_challenge,
                "version": APP_VERSION,
            },
        )
        if "token" not in auth_data:
            raise VideofiedCloudApiError(f"Missing token in auth response: {auth_data}")

        self._token = auth_data["token"]
        panels = auth_data.get("user", {}).get("panels", [])
        if not panels:
            raise VideofiedCloudApiError("No Videofied panel found on this account")
        panel = panels[0]
        self._panel_serial = panel.get("serial")
        self._panel_name = panel.get("name")
        self._host = panel.get("ecosystem", {}).get("host")
        if not self._host:
            raise VideofiedCloudApiError("Missing ecosystem host")

    async def ensure_authenticated(self) -> None:
        if not self._token or not self._host:
            await self.authenticate()

    async def get_panel_info(self) -> dict[str, Any]:
        await self.ensure_authenticated()
        assert self._token is not None
        try:
            data = await self._post_json(f"{self.host}/node-app/getpanelinfo", {"token": self._token})
        except VideofiedCloudApiError:
            await self.authenticate()
            assert self._token is not None
            data = await self._post_json(f"{self.host}/node-app/getpanelinfo", {"token": self._token})
        return data

    async def get_events_list(self, offset: int = 0, media_only: bool = False) -> list[dict[str, Any]]:
        await self.ensure_authenticated()
        assert self._token is not None
        data = await self._post_json(
            f"{self.host}/node-app/getEventsList",
            {"token": self._token, "offset": offset, "mediaOnly": media_only},
        )
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def take_picture(self, camera_index: str | int) -> dict[str, Any]:
        await self.ensure_authenticated()
        assert self._token is not None
        return await self._post_json(
            f"{self.host}/node-app/takePicture",
            {"token": self._token, "camera_index": str(camera_index)},
        )

    async def get_latest_picture_event(self, camera_index: str | int | None = None) -> dict[str, Any] | None:
        events = await self.get_events_list(offset=0, media_only=False)
        for event in events:
            if event.get("Event") != "PictureReceived":
                continue
            if camera_index is not None and str(event.get("Camera")) != str(camera_index):
                continue
            if event.get("PictureURI") and event.get("PictureToken"):
                return event
        return None

    async def download_picture(self, picture_uri: str, picture_token: str) -> bytes:
        await self.ensure_authenticated()
        uri = quote(f"{picture_uri}?authenticationbearer={picture_token}", safe="")
        url = f"{self.host}/node-app/proxy?uri={uri}"
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            data = await resp.read()
            if resp.status >= 400:
                raise VideofiedCloudApiError(f"HTTP {resp.status}: {data[:200]!r}")
            return data

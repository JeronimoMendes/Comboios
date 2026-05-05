import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from comboios.exceptions import AuthenticationError

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://www.cp.pt",
    "Referer": "https://www.cp.pt/",
}

_CONFIG_URL = "https://www.cp.pt/fe-config.json"
_DEFAULT_TTL_SECONDS = 3600


@dataclass(frozen=True)
class CpCredentials:
    travel_api_url: str
    travel_api_key: str
    xcck: str
    xccs: str


class CpConfigProvider:
    def __init__(self, ttl_seconds: float | None = None) -> None:
        self._ttl_seconds = ttl_seconds or float(
            os.environ.get("COMBOIOS_CACHE_TTL", _DEFAULT_TTL_SECONDS)
        )
        self._credentials: CpCredentials | None = None
        self._expires_at: datetime | None = None

    async def get_credentials(self) -> CpCredentials:
        if self._credentials is not None and self._expires_at is not None:
            if datetime.now(timezone.utc) < self._expires_at:
                return self._credentials
        await self.refresh()
        if self._credentials is None:
            raise AuthenticationError("Failed to fetch credentials")
        return self._credentials

    async def refresh(self) -> None:
        async with httpx.AsyncClient(headers=_BROWSER_HEADERS, timeout=15.0) as client:
            try:
                resp = await client.get(_CONFIG_URL)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise AuthenticationError(f"Failed to fetch fe-config.json: {exc}") from exc

        data = resp.json()
        try:
            self._credentials = CpCredentials(
                travel_api_url=data["travelApiUrl"],
                travel_api_key=data["travelApiKey"],
                xcck=data["xcck"],
                xccs=data["xccs"],
            )
        except KeyError as exc:
            raise AuthenticationError(f"Missing key in fe-config.json: {exc}") from exc

        self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl_seconds)

    def invalidate_cache(self) -> None:
        self._credentials = None
        self._expires_at = None

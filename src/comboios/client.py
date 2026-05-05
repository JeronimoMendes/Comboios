from __future__ import annotations

from typing import Any

import httpx

from comboios.config import CpConfigProvider
from comboios.exceptions import APIError, NotFoundError

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://www.cp.pt",
    "Referer": "https://www.cp.pt/",
}

_DEFAULT_BASE_URL = "https://api-gateway.cp.pt/cp/services/travel-api"


class ComboiosClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        provider: CpConfigProvider | None = None,
    ) -> None:
        self._base_url = (base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._provider = provider or CpConfigProvider()
        self._sync_client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    def _sync(self) -> httpx.Client:
        if self._sync_client is None:
            self._sync_client = httpx.Client(timeout=self._timeout)
        return self._sync_client

    def _async(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self._timeout)
        return self._async_client

    async def _auth_headers(self) -> dict[str, str]:
        creds = await self._provider.get_credentials()
        return {
            **_BROWSER_HEADERS,
            "x-api-key": creds.travel_api_key,
            "x-cp-connect-id": creds.xcck,
            "x-cp-connect-secret": creds.xccs,
        }

    def _auth_headers_sync(self) -> dict[str, str]:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            raise RuntimeError(
                "Synchronous auth headers cannot be fetched from an async context. "
                "Use async methods instead."
            )

        creds = asyncio.run(self._provider.get_credentials())
        return {
            **_BROWSER_HEADERS,
            "x-api-key": creds.travel_api_key,
            "x-cp-connect-id": creds.xcck,
            "x-cp-connect-secret": creds.xccs,
        }

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        url = f"{self._base_url}/{path.lstrip('/')}"
        headers = await self._auth_headers()
        request_kwargs = {**kwargs, "headers": headers}

        client = self._async()
        response = await client.request(method, url, **request_kwargs)

        if response.status_code in (401, 403):
            self._provider.invalidate_cache()
            headers = await self._auth_headers()
            request_kwargs = {**kwargs, "headers": headers}
            response = await client.request(method, url, **request_kwargs)

        if response.status_code == 404:
            raise NotFoundError(f"{method} {path} returned 404")
        if response.status_code >= 400:
            raise APIError(
                f"{method} {path} returned {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        return response

    def _request_with_retry_sync(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        url = f"{self._base_url}/{path.lstrip('/')}"
        headers = self._auth_headers_sync()
        request_kwargs = {**kwargs, "headers": headers}

        client = self._sync()
        response = client.request(method, url, **request_kwargs)

        if response.status_code in (401, 403):
            self._provider.invalidate_cache()
            headers = self._auth_headers_sync()
            request_kwargs = {**kwargs, "headers": headers}
            response = client.request(method, url, **request_kwargs)

        if response.status_code == 404:
            raise NotFoundError(f"{method} {path} returned 404")
        if response.status_code >= 400:
            raise APIError(
                f"{method} {path} returned {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        return response

    # --- sync wrappers ---
    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry_sync("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry_sync("POST", path, **kwargs)

    # --- async wrappers ---
    async def aget(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("GET", path, **kwargs)

    async def apost(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("POST", path, **kwargs)

    async def aclose(self) -> None:
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    def close(self) -> None:
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    def __enter__(self) -> ComboiosClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    async def __aenter__(self) -> ComboiosClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

import pytest
import respx
from httpx import Response

from comboios.config import CpConfigProvider
from comboios.exceptions import AuthenticationError


@respx.mock
async def test_get_credentials_success() -> None:
    route = respx.get("https://www.cp.pt/fe-config.json").mock(
        return_value=Response(
            200,
            json={
                "travelApiUrl": "https://api.example.com",
                "travelApiKey": "key-123",
                "xcck": "xcck-123",
                "xccs": "xccs-123",
            },
        )
    )
    provider = CpConfigProvider(ttl_seconds=60)
    creds = await provider.get_credentials()
    assert creds.travel_api_url == "https://api.example.com"
    assert creds.travel_api_key == "key-123"
    assert creds.xcck == "xcck-123"
    assert creds.xccs == "xccs-123"
    assert route.called


@respx.mock
async def test_get_credentials_uses_cache() -> None:
    route = respx.get("https://www.cp.pt/fe-config.json").mock(
        return_value=Response(
            200,
            json={
                "travelApiUrl": "https://api.example.com",
                "travelApiKey": "key-123",
                "xcck": "xcck-123",
                "xccs": "xccs-123",
            },
        )
    )
    provider = CpConfigProvider(ttl_seconds=60)
    await provider.get_credentials()
    await provider.get_credentials()
    assert route.call_count == 1


@respx.mock
async def test_get_credentials_refreshes_after_invalidate() -> None:
    route = respx.get("https://www.cp.pt/fe-config.json").mock(
        return_value=Response(
            200,
            json={
                "travelApiUrl": "https://api.example.com",
                "travelApiKey": "key-123",
                "xcck": "xcck-123",
                "xccs": "xccs-123",
            },
        )
    )
    provider = CpConfigProvider(ttl_seconds=60)
    await provider.get_credentials()
    provider.invalidate_cache()
    await provider.get_credentials()
    assert route.call_count == 2


@respx.mock
async def test_get_credentials_missing_key() -> None:
    respx.get("https://www.cp.pt/fe-config.json").mock(
        return_value=Response(200, json={"travelApiUrl": "https://api.example.com"})
    )
    provider = CpConfigProvider()
    with pytest.raises(AuthenticationError):
        await provider.get_credentials()


@respx.mock
async def test_get_credentials_http_error() -> None:
    respx.get("https://www.cp.pt/fe-config.json").mock(return_value=Response(500))
    provider = CpConfigProvider()
    with pytest.raises(AuthenticationError):
        await provider.get_credentials()

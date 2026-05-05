import pytest
import respx
from httpx import Response

from comboios.client import ComboiosClient
from comboios.exceptions import APIError, NotFoundError


@pytest.fixture
def mock_config() -> None:
    with respx.mock:
        respx.get("https://www.cp.pt/fe-config.json").mock(
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
        yield


@respx.mock
async def test_aget_success() -> None:
    respx.get("https://www.cp.pt/fe-config.json").mock(
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
    route = respx.get("https://api.example.com/stations").mock(
        return_value=Response(200, json=[{"code": "94-1", "designation": "Test"}])
    )
    async with ComboiosClient(base_url="https://api.example.com") as client:
        resp = await client.aget("/stations")
        assert resp.status_code == 200
        assert route.called
        assert "x-api-key" in route.calls[0].request.headers


@respx.mock
async def test_retry_on_401() -> None:
    respx.get("https://www.cp.pt/fe-config.json").mock(
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
    route = respx.get("https://api.example.com/stations").mock(
        side_effect=[Response(401), Response(200, json=[])],
    )
    async with ComboiosClient(base_url="https://api.example.com") as client:
        resp = await client.aget("/stations")
        assert resp.status_code == 200
        assert route.call_count == 2


@respx.mock
async def test_not_found_raises() -> None:
    respx.get("https://www.cp.pt/fe-config.json").mock(
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
    respx.get("https://api.example.com/stations/94-1").mock(return_value=Response(404))
    async with ComboiosClient(base_url="https://api.example.com") as client:
        with pytest.raises(NotFoundError):
            await client.aget("/stations/94-1")


@respx.mock
async def test_api_error_raises() -> None:
    respx.get("https://www.cp.pt/fe-config.json").mock(
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
    respx.get("https://api.example.com/stations").mock(return_value=Response(500, text="error"))
    async with ComboiosClient(base_url="https://api.example.com") as client:
        with pytest.raises(APIError):
            await client.aget("/stations")

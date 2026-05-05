import pytest
import respx
from httpx import Response

from comboios.client import ComboiosClient
from comboios.endpoints.journeys import JourneysAPI
from comboios.endpoints.stations import StationsAPI
from comboios.endpoints.trains import TrainsAPI


@pytest.fixture
async def client() -> ComboiosClient:
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
    return ComboiosClient(base_url="https://api.example.com")


@respx.mock
async def test_stations_list_all(client: ComboiosClient) -> None:
    route = respx.get("https://api.example.com/stations").mock(
        return_value=Response(
            200,
            json=[
                {"code": "94-1", "designation": "Lisboa", "region": "Lisboa"},
                {"code": "94-2", "designation": "Porto", "region": "Porto"},
            ],
        )
    )
    api = StationsAPI(client)
    stations = await api.list_all()
    assert len(stations) == 2
    assert stations[0].code == "94-1"
    assert route.called


@respx.mock
async def test_stations_search(client: ComboiosClient) -> None:
    respx.get("https://api.example.com/stations").mock(
        return_value=Response(
            200,
            json=[
                {"code": "94-1", "designation": "Lisboa"},
                {"code": "94-2", "designation": "Porto"},
                {"code": "94-3", "designation": "Porto Sao Bento"},
            ],
        )
    )
    api = StationsAPI(client)
    results = await api.search("Porto")
    assert len(results) == 2
    assert results[0].code == "94-2"


@respx.mock
async def test_stations_get_timetable(client: ComboiosClient) -> None:
    route = respx.get("https://api.example.com/stations/94-1/timetable/2026-05-05").mock(
        return_value=Response(
            200,
            json={
                "stationStops": [
                    {
                        "trainNumber": 123,
                        "trainService": {"code": "AP", "designation": "Alfa Pendular"},
                        "trainOrigin": {"code": "94-2", "designation": "Porto"},
                        "trainDestination": {"code": "94-1", "designation": "Lisboa"},
                        "departureTime": "12:00",
                        "platform": "1",
                    }
                ]
            },
        )
    )
    api = StationsAPI(client)
    board = await api.get_timetable("94-1", "2026-05-05")
    assert len(board.station_stops) == 1
    assert board.station_stops[0].train_number == 123
    assert route.called


@respx.mock
async def test_trains_get_journey(client: ComboiosClient) -> None:
    route = respx.get("https://api.example.com/trains/131/timetable/2026-05-05").mock(
        return_value=Response(
            200,
            json={
                "trainNumber": 131,
                "serviceCode": {"code": "AP", "designation": "Alfa Pendular"},
                "hasDisruptions": False,
                "trainStops": [
                    {
                        "station": {"code": "94-1", "designation": "Lisboa"},
                        "departure": "07:00",
                        "platform": "1",
                    },
                    {
                        "station": {"code": "94-2", "designation": "Porto"},
                        "arrival": "10:00",
                        "platform": "2",
                    },
                ],
            },
        )
    )
    api = TrainsAPI(client)
    journey = await api.get_journey("131", "2026-05-05")
    assert journey.train_number == 131
    assert len(journey.train_stops) == 2
    assert route.called


@respx.mock
async def test_journeys_search(client: ComboiosClient) -> None:
    route = respx.post("https://api.example.com/journeys").mock(
        return_value=Response(
            200,
            json={
                "departureStation": {"code": "94-1", "designation": "Lisboa"},
                "arrivalStation": {"code": "94-2", "designation": "Porto"},
                "travelDate": "2026-05-05",
                "outwardTrip": [
                    {
                        "arrivalTime": "10:00",
                        "departureTime": "07:00",
                        "duration": "03h00",
                        "services": "AP",
                        "transferCount": 0,
                        "saleableOnline": True,
                        "basePrices": [
                            {
                                "travelClass": 2,
                                "priceType": 1,
                                "centsValue": 2500,
                                "constraints": [],
                            }
                        ],
                        "travelSections": [
                            {
                                "sequenceNumber": 1,
                                "trainNumber": 131,
                                "serviceCode": {"code": "AP", "designation": "Alfa Pendular"},
                                "departureStation": {"code": "94-1", "designation": "Lisboa"},
                                "arrivalStation": {"code": "94-2", "designation": "Porto"},
                                "trainStops": [],
                                "arrivalTime": "10:00",
                                "departureTime": "07:00",
                                "duration": "03h00",
                            }
                        ],
                    }
                ],
            },
        )
    )
    api = JourneysAPI(client)
    result = await api.search("94-1", "94-2", "2026-05-05")
    assert result.departure_station.code == "94-1"
    assert len(result.outward_trip) == 1
    assert result.outward_trip[0].base_prices[0].cents_value == 2500
    assert route.called

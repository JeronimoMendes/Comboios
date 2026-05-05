import pytest

from comboios.client import ComboiosClient
from comboios.endpoints.journeys import JourneysAPI
from comboios.endpoints.stations import StationsAPI
from comboios.endpoints.trains import TrainsAPI

pytestmark = pytest.mark.integration


@pytest.fixture
async def client() -> ComboiosClient:
    return ComboiosClient()


@pytest.mark.integration
async def test_live_stations_list(client: ComboiosClient) -> None:
    api = StationsAPI(client)
    stations = await api.list_all()
    assert len(stations) > 0
    assert stations[0].code.startswith("94-")


@pytest.mark.integration
async def test_live_timetable(client: ComboiosClient) -> None:
    api = StationsAPI(client)
    board = await api.get_timetable("94-31039", "2026-05-05", "14:00")
    assert len(board.station_stops) > 0


@pytest.mark.integration
async def test_live_train_journey(client: ComboiosClient) -> None:
    api = TrainsAPI(client)
    journey = await api.get_journey("131", "2026-05-05")
    assert journey.train_number == 131
    assert len(journey.train_stops) > 0


@pytest.mark.integration
async def test_live_journey_search(client: ComboiosClient) -> None:
    api = JourneysAPI(client)
    result = await api.search("94-7005", "94-32185", "2026-05-05", "14:00")
    assert len(result.outward_trip) > 0
    assert result.outward_trip[0].travel_sections

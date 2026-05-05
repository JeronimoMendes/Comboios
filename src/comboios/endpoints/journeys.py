from __future__ import annotations

from comboios.client import ComboiosClient
from comboios.models import JourneySearchRequest, JourneySearchResult


class JourneysAPI:
    def __init__(self, client: ComboiosClient) -> None:
        self._client = client

    async def search(
        self,
        origin_id: str,
        destination_id: str,
        date: str,
        time: str | None = None,
        travel_class: int = 2,
        passengers: int = 1,
    ) -> JourneySearchResult:
        time_limit: dict[str, object] = {
            "endTime": "23:59",
            "limitType": 2,
            "startTime": time or "00:00",
        }
        payload = JourneySearchRequest(
            arrivalStationCode=destination_id,
            departureStationCode=origin_id,
            travelDate=date,
            classes=[travel_class],
            quantities=[{"quantity": passengers, "type": 1}],
            timeLimit=time_limit,
        )
        resp = await self._client.apost("/journeys", json=payload.model_dump(by_alias=True))
        return JourneySearchResult.model_validate(resp.json())

    def search_sync(
        self,
        origin_id: str,
        destination_id: str,
        date: str,
        time: str | None = None,
        travel_class: int = 2,
        passengers: int = 1,
    ) -> JourneySearchResult:
        time_limit: dict[str, object] = {
            "endTime": "23:59",
            "limitType": 2,
            "startTime": time or "00:00",
        }
        payload = JourneySearchRequest(
            arrivalStationCode=destination_id,
            departureStationCode=origin_id,
            travelDate=date,
            classes=[travel_class],
            quantities=[{"quantity": passengers, "type": 1}],
            timeLimit=time_limit,
        )
        resp = self._client.post("/journeys", json=payload.model_dump(by_alias=True))
        return JourneySearchResult.model_validate(resp.json())

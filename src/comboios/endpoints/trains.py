from __future__ import annotations

from comboios.client import ComboiosClient
from comboios.models import TrainJourney


class TrainsAPI:
    def __init__(self, client: ComboiosClient) -> None:
        self._client = client

    async def get_journey(self, train_number: str, date: str) -> TrainJourney:
        resp = await self._client.aget(f"/trains/{train_number}/timetable/{date}")
        return TrainJourney.model_validate(resp.json())

    def get_journey_sync(self, train_number: str, date: str) -> TrainJourney:
        resp = self._client.get(f"/trains/{train_number}/timetable/{date}")
        return TrainJourney.model_validate(resp.json())

from __future__ import annotations

from comboios.client import ComboiosClient
from comboios.models import Station, StationBoard


class StationsAPI:
    def __init__(self, client: ComboiosClient) -> None:
        self._client = client

    async def list_all(self) -> list[Station]:
        resp = await self._client.aget("/stations")
        return [Station.model_validate(item) for item in resp.json()]

    def list_all_sync(self) -> list[Station]:
        resp = self._client.get("/stations")
        return [Station.model_validate(item) for item in resp.json()]

    async def search(self, query: str) -> list[Station]:
        all_stations = await self.list_all()
        query_lower = query.lower()
        return [s for s in all_stations if query_lower in s.designation.lower()]

    def search_sync(self, query: str) -> list[Station]:
        all_stations = self.list_all_sync()
        query_lower = query.lower()
        return [s for s in all_stations if query_lower in s.designation.lower()]

    async def get_timetable(
        self, station_id: str, date: str, start_time: str | None = None
    ) -> StationBoard:
        params = {}
        if start_time is not None:
            params["start"] = start_time
        resp = await self._client.aget(f"/stations/{station_id}/timetable/{date}", params=params)
        return StationBoard.model_validate(resp.json())

    def get_timetable_sync(
        self, station_id: str, date: str, start_time: str | None = None
    ) -> StationBoard:
        params = {}
        if start_time is not None:
            params["start"] = start_time
        resp = self._client.get(f"/stations/{station_id}/timetable/{date}", params=params)
        return StationBoard.model_validate(resp.json())

from __future__ import annotations

from pydantic import BaseModel, Field


class StationSimple(BaseModel):
    code: str
    designation: str


class Station(BaseModel):
    code: str
    designation: str
    latitude: str | None = None
    longitude: str | None = None
    region: str | None = None
    railways: list[str] = Field(default_factory=list)


class ServiceCode(BaseModel):
    code: str
    designation: str


class StationStop(BaseModel):
    train_number: int = Field(alias="trainNumber")
    train_service: ServiceCode = Field(alias="trainService")
    train_origin: StationSimple = Field(alias="trainOrigin")
    train_destination: StationSimple = Field(alias="trainDestination")
    arrival_time: str | None = Field(alias="arrivalTime", default=None)
    departure_time: str | None = Field(alias="departureTime", default=None)
    platform: str | None = None
    delay: int | None = None
    occupancy: int | None = None
    supression: str | None = None
    eta: str | None = Field(alias="ETA", default=None)
    etd: str | None = Field(alias="ETD", default=None)


class StationBoard(BaseModel):
    station_stops: list[StationStop] = Field(alias="stationStops")


class JourneyStop(BaseModel):
    station: StationSimple
    arrival: str | None = None
    departure: str | None = None
    platform: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    delay: int | None = None
    supression: str | None = None
    eta: str | None = Field(alias="ETA", default=None)
    etd: str | None = Field(alias="ETD", default=None)


class TrainJourney(BaseModel):
    train_number: int = Field(alias="trainNumber")
    service_code: ServiceCode = Field(alias="serviceCode")
    last_station_code: str | None = Field(
        alias="lastStationCode", default=None)
    delay: int | None = None
    occupancy: int | None = None
    latitude: str | None = None
    longitude: str | None = None
    status: str | None = None
    has_disruptions: bool = Field(alias="hasDisruptions")
    duration: str | None = None
    bike: bool | None = None
    mobility: int | None = None
    ecology: int | None = None
    messages: list[str] = Field(default_factory=list)
    train_stops: list[JourneyStop] = Field(alias="trainStops")


class BasePrice(BaseModel):
    travel_class: int = Field(alias="travelClass")
    price_type: int = Field(alias="priceType")
    cents_value: int = Field(alias="centsValue")
    constraints: list[str] = Field(default_factory=list)


class TravelSection(BaseModel):
    sequence_number: int = Field(alias="sequenceNumber")
    train_number: int = Field(alias="trainNumber")
    service_code: ServiceCode = Field(alias="serviceCode")
    departure_station: StationSimple = Field(alias="departureStation")
    arrival_station: StationSimple = Field(alias="arrivalStation")
    train_stops: list[JourneyStop] = Field(alias="trainStops")
    arrival_time: str = Field(alias="arrivalTime")
    departure_time: str = Field(alias="departureTime")
    duration: str
    departure_platform: str | None = Field(
        alias="departurePlatform", default=None)
    arrival_platform: str | None = Field(alias="arrivalPlatform", default=None)
    delay: int | None = None
    occupancy: int | None = None
    allocation: str | None = None
    bike: bool | None = None
    mobility: int | None = None
    status: str | None = None
    messages: list[str] = Field(default_factory=list)
    eta: str | None = Field(alias="ETA", default=None)
    etd: str | None = Field(alias="ETD", default=None)


class JourneyOption(BaseModel):
    arrival_time: str = Field(alias="arrivalTime")
    departure_time: str = Field(alias="departureTime")
    duration: str
    services: str
    transfer_count: int = Field(alias="transferCount")
    saleable_online: bool = Field(alias="saleableOnline")
    sale_link: str | None = Field(alias="saleLink", default=None)
    delay: int | None = None
    bike: bool | None = None
    mobility: int | None = None
    occupancy: int | None = None
    allocation: str | None = None
    ecology: int | None = None
    base_prices: list[BasePrice] = Field(
        alias="basePrices", default_factory=list)
    travel_sections: list[TravelSection] = Field(alias="travelSections")


class JourneySearchResult(BaseModel):
    departure_station: StationSimple = Field(alias="departureStation")
    arrival_station: StationSimple = Field(alias="arrivalStation")
    travel_date: str = Field(alias="travelDate")
    return_date: str | None = Field(alias="returnDate", default=None)
    outward_trip: list[JourneyOption] = Field(alias="outwardTrip")
    return_trip: list[JourneyOption] = Field(
        alias="returnTrip", default_factory=list)
    messages: list[str] = Field(default_factory=list)


class JourneySearchRequest(BaseModel):
    arrival_station_code: str = Field(alias="arrivalStationCode")
    classes: list[int]
    config_id: int = Field(alias="configID", default=200)
    departure_station_code: str = Field(alias="departureStationCode")
    lang: str = "PT"
    quantities: list[dict]
    return_date: str | None = Field(alias="returnDate", default=None)
    return_time_limit: dict = Field(
        alias="returnTimeLimit",
        default_factory=lambda: {
            "endTime": "23:59",
            "limitType": 0,
            "startTime": "00:00",
        },
    )
    saleable_only: bool = Field(alias="saleableOnly", default=False)
    search_type: int = Field(alias="searchType", default=3)
    services: list[str] = Field(default_factory=list)
    time_limit: dict = Field(
        alias="timeLimit",
        default_factory=lambda: {
            "endTime": "23:59",
            "limitType": 2,
            "startTime": "00:00",
        },
    )
    travel_date: str = Field(alias="travelDate")
    username: str = "sivNetticket"

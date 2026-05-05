from __future__ import annotations

import json
import sys
from datetime import date
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from comboios.client import ComboiosClient
from comboios.config import CpConfigProvider
from comboios.endpoints.journeys import JourneysAPI
from comboios.endpoints.stations import StationsAPI
from comboios.endpoints.trains import TrainsAPI
from comboios.models import JourneyOption, Station, StationStop, TrainJourney

app = typer.Typer(name="comboios", no_args_is_help=True)
console = Console()
err_console = Console(stderr=True)


def _is_tty() -> bool:
    return sys.stdout.isatty()


def _resolve_station(stations_api: StationsAPI, query: str) -> str:
    """Return station code if query looks like one, otherwise search by name."""
    if query.startswith("94-"):
        return query
    results = stations_api.search_sync(query)
    if not results:
        err_console.print(f"[red]No station found for '{query}'[/red]")
        raise typer.Exit(1)
    if len(results) > 1:
        err_console.print(
            f"[yellow]Multiple matches for '{query}', using first:[/yellow] "
            f"{results[0].designation}"
        )
    return results[0].code


def _output(data: object, format_mode: str | None, as_json: bool) -> None:
    if format_mode == "table":
        _rich_output(data)
    elif format_mode == "json" or as_json or not _is_tty():
        if isinstance(data, list):
            out = json.dumps(
                [_serialize(item) for item in data], indent=2, ensure_ascii=False
            )
            console.print(out)
        else:
            out = json.dumps(_serialize(data), indent=2, ensure_ascii=False)
            console.print(out)
    else:
        _rich_output(data)


def _serialize(data: object) -> object:
    if hasattr(data, "model_dump"):
        return data.model_dump(by_alias=True)
    if isinstance(data, dict):
        return {k: _serialize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize(item) for item in data]
    return data


def _rich_output(data: object) -> None:
    if isinstance(data, list) and data and isinstance(data[0], Station):
        table = Table(title="Stations")
        table.add_column("Code")
        table.add_column("Name")
        table.add_column("Region")
        for s in data:
            table.add_row(s.code, s.designation, s.region or "")
        console.print(table)
    elif isinstance(data, list) and data and isinstance(data[0], StationStop):
        table = Table(title="Timetable")
        table.add_column("Time")
        table.add_column("Train")
        table.add_column("Service")
        table.add_column("Destination")
        table.add_column("Platform")
        table.add_column("Delay")
        for stop in data:
            time = stop.departure_time or stop.arrival_time or ""
            table.add_row(
                time,
                str(stop.train_number),
                stop.train_service.code,
                stop.train_destination.designation,
                stop.platform or "",
                str(stop.delay or ""),
            )
        console.print(table)
    elif isinstance(data, TrainJourney):
        table = Table(title=f"Train {data.train_number} — {data.service_code.designation}")
        table.add_column("Station")
        table.add_column("Arrival")
        table.add_column("Departure")
        table.add_column("Platform")
        table.add_column("Delay")
        for stop in data.train_stops:
            table.add_row(
                stop.station.designation,
                stop.arrival or "",
                stop.departure or "",
                stop.platform or "",
                str(stop.delay or ""),
            )
        console.print(table)
    elif isinstance(data, list) and data and isinstance(data[0], JourneyOption):
        for opt in data:
            _print_journey_option(opt)
    else:
        console.print(data)


def _print_journey_option(opt: JourneyOption) -> None:
    price = opt.base_prices[0].cents_value / 100 if opt.base_prices else None
    price_str = f"€{price:.2f}" if price else "N/A"
    title = f"{opt.departure_time} → {opt.arrival_time}  ({opt.duration})  {price_str}"
    table = Table(title=title)
    table.add_column("#")
    table.add_column("Train")
    table.add_column("Service")
    table.add_column("From")
    table.add_column("Dep")
    table.add_column("To")
    table.add_column("Arr")
    table.add_column("Platform")
    for ts in opt.travel_sections:
        table.add_row(
            str(ts.sequence_number),
            str(ts.train_number),
            ts.service_code.code,
            ts.departure_station.designation,
            ts.departure_time,
            ts.arrival_station.designation,
            ts.arrival_time,
            ts.departure_platform or "",
        )
    console.print(table)


@app.callback()
def main(
    ctx: typer.Context,
    json_output: Annotated[
        bool, typer.Option("--json", help="Force JSON output")
    ] = False,
    format_mode: Annotated[
        str | None, typer.Option("--format", help="Output format: json or table")
    ] = None,
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="Bypass credential cache")
    ] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Verbose logging")] = False,
    timeout: Annotated[
        float, typer.Option("--timeout", help="Request timeout in seconds")
    ] = 30.0,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output
    ctx.obj["format"] = format_mode
    ctx.obj["no_cache"] = no_cache
    ctx.obj["debug"] = debug
    ctx.obj["timeout"] = timeout


def _get_client(ctx: typer.Context) -> ComboiosClient:
    provider = CpConfigProvider()
    if ctx.obj.get("no_cache"):
        provider.invalidate_cache()
    return ComboiosClient(timeout=ctx.obj["timeout"], provider=provider)


@app.command()
def stations(
    ctx: typer.Context,
    list_all: Annotated[
        bool, typer.Option("--list", "-l", help="List all stations")
    ] = False,
    search: Annotated[
        str | None, typer.Option("--search", "-s", help="Search stations by name")
    ] = None,
    get: Annotated[
        str | None,
        typer.Option("--get", "-g", help="Get station timetable code"),
    ] = None,
) -> None:
    """List or search stations."""
    with _get_client(ctx) as client:
        api = StationsAPI(client)
        if list_all or (not search and not get):
            result = api.list_all_sync()
            _output(result, ctx.obj.get("format"), ctx.obj.get("json", False))
        elif search:
            result = api.search_sync(search)
            _output(result, ctx.obj.get("format"), ctx.obj.get("json", False))
        elif get:
            err_console.print("Use 'timetable' command for station timetables")
            raise typer.Exit(1)


@app.command()
def timetable(
    ctx: typer.Context,
    station_id: str,
    date: Annotated[
        str, typer.Option("--date", "-d", help="Date YYYY-MM-DD")
    ] = date.today().isoformat(),
    time: Annotated[
        str | None, typer.Option("--time", "-t", help="Start time HH:MM")
    ] = None,
) -> None:
    """Get station timetable."""
    with _get_client(ctx) as client:
        api = StationsAPI(client)
        board = api.get_timetable_sync(station_id, date, time)
        _output(board.station_stops, ctx.obj.get("format"), ctx.obj.get("json", False))


@app.command()
def train(
    ctx: typer.Context,
    train_number: str,
    date: Annotated[
        str, typer.Option("--date", "-d", help="Date YYYY-MM-DD")
    ] = date.today().isoformat(),
) -> None:
    """Get train journey details."""
    with _get_client(ctx) as client:
        api = TrainsAPI(client)
        journey = api.get_journey_sync(train_number, date)
        _output(journey, ctx.obj.get("format"), ctx.obj.get("json", False))


journey_app = typer.Typer()
app.add_typer(journey_app, name="journey")


@journey_app.command("search")
def journey_search(
    ctx: typer.Context,
    origin: str,
    destination: str,
    date: Annotated[
        str, typer.Option("--date", "-d", help="Date YYYY-MM-DD")
    ] = date.today().isoformat(),
    time: Annotated[
        str | None, typer.Option("--time", "-t", help="Start time HH:MM")
    ] = None,
    travel_class: Annotated[
        int, typer.Option("--class", "-c", help="Travel class (1 or 2)")
    ] = 2,
    passengers: Annotated[
        int, typer.Option("--passengers", "-p", help="Number of passengers")
    ] = 1,
) -> None:
    """Search for journeys between two stations."""
    with _get_client(ctx) as client:
        stations_api = StationsAPI(client)
        origin_id = _resolve_station(stations_api, origin)
        destination_id = _resolve_station(stations_api, destination)

        api = JourneysAPI(client)
        result = api.search_sync(
            origin_id, destination_id, date, time, travel_class, passengers
        )
        _output(result.outward_trip, ctx.obj.get("format"), ctx.obj.get("json", False))


def run() -> None:
    app()

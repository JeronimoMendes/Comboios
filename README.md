# comboios

Python CLI for querying the Comboios de Portugal (CP.pt) internal API.

## Installation

```bash
pip install comboios
```

Or with uv:

```bash
uv tool install comboios
```

## Usage

```bash
# List all stations
comboios stations --list

# Search stations
comboios stations --search "Porto"

# Station timetable
comboios timetable 94-31039 --date 2026-05-05 --time 14:00

# Train journey
comboios train 131 --date 2026-05-05

# Journey search (with station names or codes)
comboios journey search "Lisboa Oriente" "Porto Campanha" --date 2026-05-05 --time 14:00
comboios journey search 94-31039 94-2006 --date 2026-05-05

# Force JSON output
comboios --json stations --search "Porto"

# Pretty tables
comboios --format table timetable 94-31039
```

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
```

## License

MIT

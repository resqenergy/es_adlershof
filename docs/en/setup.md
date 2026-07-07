# Setup and execution

## Installation

The project requires Python 3.13 or newer. Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```bash
uv venv .venv
uv sync
```

Two dependencies are installed directly from Git:

- **npro** — `https://github.com/resqenergy/npro`
- **oemof-pipe** — `https://github.com/rl-institut/oemof_pipe`

The sources are configured in `pyproject.toml` under `[tool.uv.sources]` and are resolved automatically by `uv sync`.

## Environment variables

The script needs access to the NPRO tool using credentials.
Additionally, the paths for datasets must be set correctly.
This can be done in a `.env` file at the project root:

```ini
NPRO_EMAIL=<user>
NPRO_PASSWORD=<password>
NPRO_PROJECT=2591-13-0

NPRO_SCENARIO_DIR=datasets/npro_scenarios
NPRO_WEATHER_DIR=raw/weather
NPRO_RESULT_DIR=datasets/npro_buildings
```

The `.env` file must **not** be checked into the Git repository (see `.gitignore`). `settings.py` loads the variables automatically via `python-dotenv`.

## Makefile pipeline

The `Makefile` is the central tool for running the data pipeline.
Each target corresponds to a processing step.
Running all pipeline steps only requires `make all`.

Finally, the finished data package can be uploaded to S3 storage with `make export_datapackage`.

The project documentation can be generated locally with `make docs`.
# Installation and Setup

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

The script for generating demand time series needs access credentials for the NPRO tool.
Additionally, the paths to the data sources must be defined.
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

### Skip & Rebuild {#skip-rebuild}

Steps whose output already exists are skipped, so `make all` only computes what is missing.

- **Datasets** are complete once their metadata file exists (`datasets/<dataset>/metadata.json`, or `<output_stem>.metadata.json` for the per-scenario wasteheat files). If an upstream dataset is rebuilt, all downstream datasets are rebuilt as well.
- **`datasets/npro_buildings/`**, **`datapackages/adlershof_{YEAR}/`** and **`datapackages/adlershof_{SCENARIO}/`** are only checked for existence. They are never rebuilt automatically, in particular not the (slow) NPRO simulation.
- Changes to scripts, `raw/` or `config/` are **not** detected.

To force a rebuild, delete the dataset folder or file, or run `make -B <target>` (e.g. `make -B wasteheat_cops YEAR=2035`). Note that `-B` also rebuilds all prerequisites of the target.

Finally, the finished data package can be uploaded to S3 storage with `make export_datapackage`.

The project documentation can be generated locally with `make docs`.
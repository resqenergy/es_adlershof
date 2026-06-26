# Energysystem Adlershof

This tool builds the oemof.tabular datapackage including multiple scenarios for energysystem of Adlershof in the ResQEnergy project.

## Usage

1. Install environment and dependencies via `uv venv .venv` and `uv sync`.
2. Download/snyc raw data and store it in folder `raw`.
3. GSEE timeseries need an extra envrionment due to legacy dependencies.
   Create conda environment via: `cd scripts/pv_precalc/ && conda env create -f environment.yml`
4. Run data pipeline via `make all`
5. Export datapackage to S3 via `make export_datapackage` (or upload it manually)

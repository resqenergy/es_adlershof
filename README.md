# Energysystem Adlershof

This tool builds the oemof.tabular datapackage including multiple scenarios for energysystem of Adlershof in the ResQEnergy project.

## Usage

1. Install environment and dependencies via `uv venv .venv` and `uv sync`.
2. Download/snyc raw data and store it in folder `raw`.
3. You must prepare GSEE timeseries upfront. To do so:
   a. Create conda environment via: `cd scripts/pv_precalc/ && conda env create -f environment.yml`
   b. Activate conda environment via: `conda activate gsee37`
   c. Run pv_precalc.py via: `python calc_gsee_timeseries.py`
   d. Deactivate conda and return to the main directory: `conda deactivate && cd ../..`
4. Run data pipeline via `make all`
5. Export datapackage to S3 via `make export_datapackage` (or upload it manually)

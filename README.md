# Energysystem Adlershof

This tool builds the oemof.tabular datapackage including multiple scenarios for energysystem of Adlershof in the ResQEnergy project.

## Usage

1. Install environment and dependencies via `uv venv .venv` and `uv sync`.
2. Download raw data and store it in folder `raw`.
3. Run preprocessing scripts in the following order:
   1. `python scripts/preprocess_demands.py`
   2. `python scripts/preprocess_cops.py`
   3. `python scripts/preprocess_naming.py`
   4. `python scripts/preprocess_capacity_costs.py`
4. Create datapackage from blueprint via `uv run oemof-pipe blueprint adlershof`
5. Create scenario "2050-el_eff" (adapt for other scenario) datapackage from blueprint via `uv run oemof-pipe scenario adlershof 2050-el_eff`

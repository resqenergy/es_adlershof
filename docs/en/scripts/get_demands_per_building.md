# Create NPRO building simulations

## Purpose

Creates NPRO scenario YAML files for all combinations of climate scenario, planning horizon, and district heating supply topology. These YAML files are subsequently executed by the NPRO simulation to compute hourly demand profiles per building type.

## Inputs

| Path | Content |
|------|--------|
| `datasets/areas_forecast/total_area_and_units_central_with_forecast.csv` | Projected areas (central) |
| `datasets/areas_forecast/total_area_and_units_low_temp_central_with_forecast.csv` | Projected areas (low temperature) |
| `datasets/areas_forecast/total_area_and_units_decentral_with_forecast.csv` | Projected areas (decentral) |
| `config/building_shares.yaml` | Shares of existing vs. new buildings per planning horizon |
| NPRO weather data (`WEATHER_DIR`) | TRY weather files, managed by npro |

### `config/building_shares.yaml`

Defines the share of existing vs. new buildings per year for non-residential buildings:

| Year | Existing | New |
|------|---------|--------|
| statusquo | 100 % | 0 % |
| 2035 | 83.38 % | 16.62 % |
| 2050 | 58.44 % | 41.56 % |

## Outputs

NPRO scenario YAML files in the NPRO scenarios directory (`SCENARIOS_DIR`, managed internally by npro), one per combination of climate scenario × planning horizon × topology. File name scheme:

```
{year}_{climate_scenario}_{topology}.yaml
```

Example: `2035_mean_rcp85_central.yaml`

Each YAML file contains:

- `weather`: file name of the TRY weather file
- `buildings`: dictionary with building keys and their parameters (`based_on`, `floorArea`, `numApart`, `buildingSubtype`, etc.)

## Parameters

| Parameter | Source | Meaning |
|-----------|--------|-----------|
| Planning horizons | Hardcoded | `statusquo`, `2035`, `2050` |
| Period mapping | Hardcoded | `p1`→statusquo, `p2`→2035, `p3`→2050 |
| Topologies | Hardcoded | `central`, `decentral`, `low_temp_central` |
| Existing/new shares | `config/building_shares.yaml` | Dynamic per year |

## Algorithm

1. Iterates over all TRY weather files in the NPRO weather directory.
2. Derives planning horizon and climate scenario from the file name (period marker `p1`/`p2`/`p3` and climate designation).
3. For each weather file × topology combination:
   - Loads the projected area CSV for the corresponding topology.
   - For residential buildings, a single entry with total area and units is created (`numApart`, `shOption: heatLoad`).
   - For non-residential buildings, the number of new buildings is computed via `building_shares.yaml`. Existing and new buildings receive separate entries with the suffix `_existing` or `_new` and their respective `buildingSubtype`.
   - Entries with 0 usable floor area or 0 new units are skipped.
4. Writes the finished scenario as a YAML file to the NPRO scenarios directory.

## Dependencies

- **npro** (Git: [resqenergy/npro](https://github.com/resqenergy/npro)) — building energy simulation tool by ResQEnergy. This script generates the input scenarios for npro. The actual simulation is run afterwards separately with `npro run all`. npro is registered as a Git dependency in `pyproject.toml` and provides `SCENARIOS_DIR` and `WEATHER_DIR`.
- **pandas** — loading and processing area CSVs.
- **PyYAML** — writing scenario YAML files.

## Execution

```bash
make npro_scenarios   # creates the NPRO scenario YAML files
make npro_buildings   # runs the NPRO simulation (npro run all)
```

`make npro_buildings` requires `make npro_scenarios`. `make npro_scenarios` requires `make areas_forecast`.

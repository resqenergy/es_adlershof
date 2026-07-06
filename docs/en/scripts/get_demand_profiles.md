# Aggregate demand profiles

## Purpose

Aggregates the hourly demand profiles from the NPRO building simulations per scenario (climate scenario × planning horizon) and topology. Produces normalized hourly profiles (0–1) as well as a table of annual totals per demand type, prepared for further use in oemof-pipe.

## Inputs

| Path | Content |
|------|--------|
| `datasets/npro_buildings/{scenario}/` | One directory per scenario, containing a CSV and JSON file per building |

### Directory structure

```
datasets/npro_buildings/
└── 2035_mean_rcp85_central/
    ├── Büro_existing.csv
    ├── Büro_existing.json
    ├── ...
```

### Building CSV (profile data)

Each building CSV contains hourly time series with 8760 rows. Columns used:

| Column | Meaning |
|--------|-----------|
| `plugLoadsProfile` | Electrical plug-load demand \[kWh/h\] |
| `emobProfile` | Mobility demand (e-mobility) \[kWh/h\] |
| `spaceHeatProfile` | Space heating demand \[kWh/h\] |
| `dhwProfile` | Domestic hot water demand \[kWh/h\] |
| `spaceCoolProfile` | Space cooling demand \[kWh/h\] |
| `processCoolProfile` | Process cooling demand \[kWh/h\] |

### Building JSON (metadata)

Contains, among other things, `buildingType` (`residential` or non-residential), used to determine the `residential` vs. `non_residential` distinction.

## Outputs

| File | Content |
|-------|--------|
| `datasets/demand_profiles/total_demands.csv` | Annual totals per demand type and scenario, in long format |
| `datasets/demand_profiles/{year}_{climate_scenario}.csv` | Normalized hourly profiles (0–1) per scenario |

### `total_demands.csv`

| Column | Description |
|--------|-------------|
| `year_climate` | Scenario key, e.g. `2035_mean_rcp85` |
| `name` | Demand type designation, e.g. `electricity-residential-demand` |
| `amount` | Annual energy \[kWh\] |

### Normalized hourly profiles

Column naming convention:

- Heat: `heat_{topology}-{residential_type}` (e.g. `heat_central-residential`)
- All others: `{demand_type}-{residential_type}` (e.g. `electricity-non_residential`)

Each profile CSV additionally contains a `timeindex` column with hourly timestamps.

## Parameters

| Parameter | Value | Meaning |
|-----------|------|-----------|
| Time steps | 8760 | Hourly resolution (1 year) |
| Demand types | electricity, mobility, heat, cool | Combination of the CSV profiles |
| Scenario folders | All subfolders in `datasets/npro_buildings/` | Automatically detected |

The folder name is parsed following the scheme `{year}_{climate_scenario}_{topology}`.

## Algorithm

1. Iterates over all scenario subfolders in `datasets/npro_buildings/`.
2. Derives `year`, `climate_scenario`, and `topology` from the folder name.
3. For each building (JSON + CSV pair):
   - Reads the building JSON to determine `residential` vs. `non_residential`.
   - Computes four demand profiles: `electricity` (plugLoads), `mobility` (emob), `heat` (spaceHeat + dhw), `cool` (spaceCool + processCool).
   - Sums the profiles into the scenario-wide aggregates (annual totals and hourly profiles).
4. Creates `total_demands.csv` in long format (melt), with the suffix `-demand` on column names.
5. Normalizes the hourly profiles by dividing by the respective annual totals from `total_demands.csv`.
6. Sets a `DatetimeIndex` (hourly, starting January 1 of the respective year; for `statusquo`, 2025 is used as the reference year).
7. Saves one normalized profile CSV per climate scenario × planning horizon.

## Dependencies

- **pandas** — loading, aggregating, normalizing, and saving profiles.

## Execution

```bash
make demand_profiles
```

Requires `make npro_buildings`.

# Compute waste-heat capacities

## Purpose

Derives thermal capacity potentials for all waste-heat heat pump components. A distinction is made between **dynamic** sources (capacity computed from energy profile × COP) and **static** sources (capacity taken directly from the technology Excel sheet).

## Inputs

| Path | Description |
|------|-------------|
| `raw/wasteheat_potentials/Abwärmepotenziale_Adlershof.xlsx` | Annual energies and rated powers per technology and planning horizon |
| `datasets/wasteheat_cop/cop_{year}.csv` | Hourly COP time series per component |
| `datasets/wasteheat_profiles/{scenario}.csv` | Hourly energy profiles per temperature level |

## Outputs

**Path:** `datasets/wasteheat_capacity/capacity.csv`

| Column | Description |
|--------|-------------|
| `scenario` | Scenario name (e.g. `2035_mean_rcp85`) |
| `name` | Component designation (e.g. `heatpump_ht`) |
| `capacity_potential` | Thermal capacity \[kW\] |
| `full_load_time_max` | Full load hours (static sources only) \[h\] |

**Component mapping:**

| Source (Excel) | Name (output) |
|---------------|----------------|
| BTB waste-heat recovery (high temperature) | `heatpump_ht` |
| Chemical industry + industry + BTB (medium temperature) | `heatpump_mt` |
| Laundry, office, and lab | `heatpump_office` |
| Data center + BTB/industry (low temperature) | `heatpump_nt` |
| Wastewater *(static)* | `heatpump_wastewater` |
| Spree river & Teltow Canal *(static)* | `heatpump_canal` |
| Medium-deep geothermal *(static)* | `heatpump_geothermal` |

## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `PERCENTILE` | 95 | Percentile used to determine capacity from the power series |
| `YEAR_INDEX_LOOKUP` | `{2025: 0, 2035: 1, 2050: 2}` | Column index in the Excel sheet |
| `POWER_LOOKUP` | 7 | Row index of rated power in the Excel sheet |
| Scenario | `2035_mean_rcp85` (hardcoded) | Scenario to process |
| Year | `2035` (hardcoded) | Planning horizon |

## Algorithm

**Dynamic sources (HT, MT, NT, office):**

1. Load the component's energy profile and COP time series.
2. Compute hourly electrical power: `P_el = energy / COP`.
3. Determine the 95th percentile of the power series as design power.
4. Compute thermal capacity from design power × mean COP.

**Static sources (wastewater, canal, geothermal):**

1. Read rated power directly from the Excel dataset.
2. Compute full load hours from annual energy / rated power.

Results from both groups are merged and saved as CSV.

## Dependencies

**pandas** — data processing, percentile computation via `quantile()`.

**openpyxl** (transitively via pandas) — reading the Excel source file.

## Execution

```bash
make wasteheat_capacities
```

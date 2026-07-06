# Compute costs for air heat pumps

## Purpose

Determines capacities and weighted mean costs for decentral air heat pumps per scenario. Capacities are derived from NPRO building heat demands and COP profiles; costs come from the technology catalog and are weighted by usage units.

## Inputs

| Path | Description |
|------|--------------|
| `preprocessed/ts_hp_air_cop.csv` | Hourly COP time series (output of `preprocess_hp_air_cop.py`), column `heatpump_air-profile` |
| `datasets/npro_buildings/<scenario>_<topology>/` | NPRO building results per scenario and topology (CSV with `spaceHeatProfile`) |
| `datasets/areas_forecast/total_area_and_units_<topology>_with_forecast.csv` | Usage units per cluster and year |
| Technology catalog raw data | Costs for `LuftWP_dezentral` at capacity steps 5–100 kW |

## Outputs

| Path | Description |
|------|--------------|
| `datasets/heatpump_air/heatpump_air_<scenario>.csv` | Capacities and costs per cluster, topology, and scenario |
| `datasets/heatpump_air/hp_cost.csv` | Weighted mean cost parameter per scenario (one row per scenario) |

Output columns per scenario file: `Topology`, `Cluster`, `Nutzeinheiten`, `Available_Capacity`, plus cost variables from the technology catalog.

## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `TECHNIKKATALOG_HP_CAPACITIES` | `(5, 10, 20, 30, 40, 50, 60, 80, 100)` | Available heat pump capacity steps in the technology catalog \[kW\] |
| `TECHNIKKATALOG_TECHNOLOGY_NAME` | `"LuftWP_dezentral"` | Technology name in the technology catalog |

## Algorithm

**Capacity calculation per cluster and scenario:**

1. For each combination of scenario and topology (`central`, `decentral`, `low_temp_central`):
   - Sum NPRO space heating demands (`spaceHeatProfile`) per cluster
   - Compute mean heat demand per usage unit
   - Determine peak load as the maximum of `heat demand / COP`
   - Heat pump capacity = 90 % of peak load

**Cost assignment:**

2. Round the computed capacity to the nearest technology catalog capacity step
3. Retrieve costs for that capacity step from the technology catalog

**Weighted averaging:**

4. Weight all clusters by usage units → produce one representative cost value per scenario
5. Save results as CSV

## Dependencies

No external libraries beyond the project standard. Internal dependencies: `utils.technikkatalog` (technology catalog data access), `utils.files` (CSV writing).

## Execution

```bash
uv run -m scripts.preprocess_hp_air_cost
```

No standalone Makefile target. Must be run after `preprocess_hp_air_cop.py`.

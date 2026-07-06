# Compute capacity costs

## Purpose

Computes annualized capacity costs from overnight CAPEX, lifetime, WACC, and fixed operating costs. Processes two input sources: heat supply technologies from the technology catalog and solar thermal parameters.

## Inputs

| Path | Description |
|------|--------------|
| `datasets/technology_cost/kww_technikkatalog.csv` | Filtered technology data (output of `prepare_technikkatalog.py`) |
| `raw/solar_thermal/solar_thermal_parameters.csv` | Overnight CAPEX, lifetime, and fixed operating costs for solar thermal |

Both files are semicolon-separated CSVs with columns `scenario_key` (or `scenario`), `name`, `var_name`, `var_value`.

## Outputs

| Path | Description |
|------|--------------|
| `datasets/technology_capacity_cost/kww_technikkatalog_capacity_cost.csv` | Annualized capacity costs for heat technologies, per scenario and technology |
| `datasets/solar_thermal/solar_thermal_capacity_cost.csv` | Annualized capacity costs for solar thermal |

Output columns: `scenario_key` (or `scenario`), `name`, `capacity_cost`, optionally `storage_capacity_cost`.

## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `WACC` | 0.04 | Weighted average cost of capital (4 %) |

WACC is defined as a constant in the script. Lifetime and CAPEX come from the input files.

## Algorithm

The function `calculate_annual_cost` is called separately for both input files:

1. Read CSV; rows with `scenario_key == "ALL"` are excluded from the calculation (passed through unchanged)
2. Group by `(scenario_key, name)`
3. Per group:
   - Read `lifetime` from `var_name == "lifetime"`
   - Read `capacity_cost_overnight` → compute annuity: `ann = CAPEX · WACC · (1+WACC)^n / ((1+WACC)^n − 1)`
   - Add `fixom_cost` → `capacity_cost = ann + fixom`
   - Optionally: same calculation for `storage_capacity_cost_overnight`
4. Merge results into a DataFrame and save as CSV

Rows without `lifetime` or without `capacity_cost_overnight` are skipped.

## Dependencies

No external libraries beyond the project standard. Annuity calculation in `utils.economics.annuity`.

**oemof-pipe**: consumes both output files as scalar input data in the scenario YAMLs.

## Execution

```bash
make parameters
```

Equivalent to (second step): `uv run -m scripts.preprocess_capacity_costs`

Must be run after `prepare_technikkatalog.py`, since `datasets/technology_cost/kww_technikkatalog.csv` is required as input.

# Estimate Teltow Canal heat quantity

## Purpose

Estimates the mean usable heat output of the Teltow Canal as a heat source for heat pumps. Flow rate and water temperature are fetched year by year from the Berlin Water Portal, and the thermally usable power is computed assuming a constant temperature difference. The script is intended for analysis and prints results to the console.

## Inputs

All data is fetched live via HTTP POST from the Berlin Water Portal:

| Source | Station | Parameter |
|--------|---------|-----------|
| Berlin Water Portal – station 5870100 | Teltow Canal, Neukölln lock | Daily flow rate \[m³/s\] |
| Berlin Water Portal – station 5866700 | Teltow Canal | Daily water temperature \[°C\] |

Years analyzed: 2017–2025.

## Outputs

Console output only (no files). A results table and the mean usable heat output in MW are printed:

| Column | Description |
|--------|-------------|
| `Jahr` | Calendar year |
| `T_mean_°C` | Mean water temperature \[°C\] |
| `V_mean_m3s` | Mean flow rate \[m³/s\] |
| `rho_kgm3` | Density of water \[kg/m³\] |
| `cp_JkgK` | Specific heat capacity \[J/(kg·K)\] |
| `Q_nutz_MW` | Usable heat output \[MW\] |

## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `DELTA_T` | 3.0 °C | Assumed usable temperature difference |
| `years` | 2017–2025 | Analysis period |

## Algorithm

1. **Fetch data** — flow rate and temperature are loaded via HTTP POST from the Berlin Water Portal (daily mean values as CSV).
2. **Process year by year** — annual subsets are filtered from the daily data for each year.
3. **Compute means** — mean annual temperature `T_mean` and mean flow rate `V_mean`.
4. **Determine material properties** — CoolProp provides temperature-dependent water density `ρ` and specific heat capacity `cp` at mean annual temperature and standard pressure (101325 Pa).
5. **Compute heat output:**

    $$Q_\text{usable} = \rho \cdot c_p \cdot \dot{V} \cdot \Delta T$$

6. **Output** — results per year and the mean usable heat output across all years are printed to the console.

## Dependencies

**CoolProp** — thermodynamic material property library. Provides precise temperature-dependent water properties (density, heat capacity) via `PropsSI()` without tabulated approximations.

**requests** — HTTP POST requests to the Berlin Water Portal. Requires network access at runtime.

**pandas** — time series processing, per-year filtering.

## Execution

No Makefile target exists. Direct invocation:

```bash
uv run -m scripts.calc_waermemenge_teltowkanal
```

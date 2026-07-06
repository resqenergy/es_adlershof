# COP time series for waste-heat heat pumps

## Purpose

Computes hourly COP (coefficient of performance) time series for six waste-heat heat pump components. Source temperatures are partly fetched live from the Berlin Water Portal (canal), partly modeled as seasonal constants (wastewater), or assumed as fixed annual values (office, MT, NT, geothermal).

## Inputs

| Source | Description |
|--------|-------------|
| Berlin Water Portal – station 5866700 | Hourly water temperature of the Teltow Canal, fetched live via HTTP POST |

All other source temperatures are defined as constants in the script (no input files).

## Outputs

**Path:** `datasets/wasteheat_cop/cop_{year}.csv`

| Column | Source temperature | Description |
|--------|----------------|-------------|
| `heatpump_office-efficiency` | 45 °C (constant) | COP for office waste heat |
| `heatpump_mt-efficiency` | 59 °C (constant) | COP for medium-temperature waste heat |
| `heatpump_nt-efficiency` | 32 °C (constant) | COP for low-temperature waste heat |
| `heatpump_geothermal-efficiency` | 22 °C (constant) | COP for geothermal |
| `heatpump_canal-efficiency` | Live canal data \[K\] | COP for Teltow Canal |
| `heatpump_wastewater-efficiency` | Seasonal: 13.5 °C / 18.5 °C | COP for wastewater |

## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `TARGET_TEMPERATURE` | 88 °C (361.15 K) | Supply temperature of the heating network |
| `QUALITY_GRADE` | 0.4 | Quality grade (Carnot efficiency factor) |
| `YEAR` | e.g. `2035` | Calendar year for time index and fetch start date |

**Seasonal wastewater temperatures:**

| Months | Temperature |
|--------|-----------|
| Jan–Mar, Oct–Dec | 13.5 °C (mean of 12–15 °C) |
| Apr–Sep | 18.5 °C (mean of 17–20 °C) |

## Algorithm

1. **Fetch canal data** — hourly water temperatures are fetched via HTTP POST from `wasserportal.berlin.de` (station 5866700), resampled to hourly means, truncated to 8760 values, and converted to Kelvin.
2. **Construct wastewater temperature** — seasonal temperature arrays (Jan–Mar, Apr–Sep, Oct–Dec) are assembled into an 8760-hour time series.
3. **Assemble source temperatures** — source temperatures (constant or time-dependent) are provided as a `pd.Series` for all six components.
4. **Compute COP** — for each component:

    $$\text{COP} = \eta_\text{quality} \cdot \frac{T_\text{target}}{T_\text{target} - T_\text{source}}$$

5. **Save** — all six COP series as CSV with `timeindex`.

## Dependencies

**requests** — HTTP POST requests to the Berlin Water Portal. Requires network access at runtime.

**pandas** — time series resampling, DataFrame creation.

## Execution

```bash
make wasteheat_cops YEAR=2035
```

# Compute wind power time series

## Purpose

Computes normalized hourly wind power time series from TRY weather data (test reference years) for each available climate path. Each weather file produces one normalized time series (0–1), used directly as `wind-profile` in oemof-tabular data packages.

## Inputs

| Path | Description |
|------|--------------|
| `raw/weather/*.csv` | TRY weather data (semicolon-separated), one file per climate scenario and period |
| `raw/wind_turbine_models/Distributed/2019COE_DW100_100kW_27.6.csv` | NREL power curve of the modeled wind turbine |

The TRY files contain hourly values for air pressure (`pressure_surface`), wind speed (`wind_speed`), and air temperature (`air_temperature_mean`). The measurement period is derived from the file name:

| File name marker | Calendar year |
|-------------------|-------------|
| `p1` | 2020 |
| `p2` | 2035 |
| `p3` | 2050 |
| `reference` | 2011 |

## Outputs

**Path:** `datasets/wind_profiles/wind_timeseries-{filename}-{year}.csv`

One CSV file is generated per TRY weather file, with two columns:

| Column | Description |
|--------|-------------|
| `timeindex` | Hourly timestamp |
| `wind_profile` | Normalized wind power \[0–1\] (rounded to 7 decimal places) |

## Parameters

The most important parameters are defined in the `args` dict and in `modelchain_data` at the top of the script:

**Turbine parameters (`args`):**

| Parameter | Value | Description |
|-----------|------|-------------|
| `wind_turbine_name` | `2019COE_DW100_100kW_27.6` | NREL turbine model |
| `wind_turbine_class` | `Distributed` | Turbine class (subfolder in `wind_turbine_models/`) |
| `wind_turbine_hub_height` | `40` m | Hub height |
| `wind_turbine_nominal_power` | `100000` W (100 kW) | Rated power used for normalization |
| `coords` | `(52.43, 13.54)` | Coordinates of Adlershof (Berlin) |
| `roughness_length` | `0.6` m | Terrain roughness length |
| `periods` | `8760` | Hours per year |

**ModelChain parameters (`modelchain_data`):**

| Parameter | Value |
|-----------|------|
| `wind_speed_model` | `logarithmic` |
| `density_model` | `barometric` |
| `temperature_model` | `linear_gradient` |
| `power_output_model` | `power_curve` |
| `density_correction` | `False` |

## Algorithm

1. **Load turbine power curve** — the NREL CSV is read and converted from kW to W. A `WindTurbine` object is initialized.
2. **Iterate weather files** — all `.csv` files in `raw/weather/` are processed one by one.
3. **Preprocess weather data** — relevant columns are selected, temperature is converted from °C to Kelvin, a constant roughness length is added, and a `MultiIndex` DataFrame for windpowerlib is created. The calendar year is derived from the file name (`p1`/`p2`/`p3`).
4. **Run ModelChain** — windpowerlib's `ModelChain` computes the turbine's hourly power output based on wind profile, density, and power curve.
5. **Normalize** — the power series is divided by rated power and rounded to 7 places.
6. **Save** — output as CSV with `timeindex` and `wind_profile`.

## Dependencies

**windpowerlib** — Python library for simulating wind turbines. Uses a `ModelChain` approach: weather preprocessing → `WindTurbine` initialization → `ModelChain.run_model()` → power output. Supports various wind profile, density, and power output models.

## Execution

No separate Makefile target exists. Direct invocation:

```bash
uv run -m scripts.calc_wind_timeseries
```

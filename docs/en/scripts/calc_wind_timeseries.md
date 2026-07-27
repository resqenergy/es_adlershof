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

The marker is matched as a standalone token, split on `.` and `_` (e.g. `rcp26.p3` or `mean_reference`), so a scenario name like `rcp26` does not accidentally match the `p2` marker.

## Outputs

**Path:** `datasets/wind_profiles/wind_timeseries-{filename}-{year}.csv`

One CSV file is generated per TRY weather file, with two columns:

| Column | Description |
|--------|-------------|
| `timeindex` | Hourly timestamp |
| `wind_profile` | Normalized wind power \[0–1\] (rounded to 7 decimal places) |

## Parameters

The most important parameters are defined in four config dicts at the top of the script:

**Run parameters (`RUN_CONFIG_DATA`):**

| Parameter | Value | Description |
|-----------|------|-------------|
| `year` | `None` | Optional explicit calendar year override. Mutually exclusive with a period marker (`p1`/`p2`/`p3`/`reference`) in the file name |
| `periods` | `8760` | Hours per year |

**Site parameters (`SITE_CONFIG_DATA`):**

| Parameter | Value | Description |
|-----------|------|-------------|
| `coords` | `(52.43, 13.54)` | Coordinates of Adlershof (Berlin) |
| `roughness_length` | `0.091` m | Local urban terrain roughness length (source: TUB.Klima measurements, median) |
| `roughness_length_freifeld` | `0.03` m | Open-terrain ("freifeld") roughness length matching the TRY reference exposure (WMO standard) |
| `displacement_height` | `16.57` m | Local urban zero-plane displacement height (source: TUB.Klima measurements, median) |
| `blending_height` | `60` m | Height at which the wind speed extrapolation switches from open-terrain to local urban parameters (see Algorithm, step 3) |

**Turbine parameters (`WIND_TURBINE_DATA`):**

| Parameter | Value | Description |
|-----------|------|-------------|
| `wind_turbine_name` | `2019COE_DW100_100kW_27.6` | NREL turbine model |
| `wind_turbine_class` | `Distributed` | Turbine class (subfolder in `wind_turbine_models/`) |
| `wind_turbine_hub_height` | `40` m | Hub height |
| `wind_turbine_nominal_power` | `100000` W (100 kW) | Rated power used for normalization |

**ModelChain parameters (`MODELCHAIN_DATA`):**

| Parameter | Value |
|-----------|------|
| `wind_speed_model` | `logarithmic` |
| `density_model` | `barometric` |
| `temperature_model` | `linear_gradient` |
| `power_output_model` | `power_curve` |
| `density_correction` | `False` |
| `obstacle_height` | `displacement_height / 0.7` | derived so that windpowerlib's internal `d = 0.7 · obstacle_height` reproduces the measured `displacement_height` |

## Algorithm

1. **Load turbine power curve** — the NREL CSV is read and converted from kW to W. A `WindTurbine` object is initialized.
2. **Iterate weather files** — all `.csv` files in `raw/weather/` are processed one by one.
3. **Preprocess weather data** — relevant columns are selected, temperature is converted from °C to Kelvin, a constant roughness length is added, and a `MultiIndex` DataFrame for windpowerlib is created. The calendar year is derived from the file name (`p1`/`p2`/`p3`/`reference`).

   The raw TRY wind speed is measured at 10 m under WMO open-terrain exposure, not the actual local urban surface, so it cannot be extrapolated directly to hub height with the local (urban) roughness length and displacement height — since `displacement_height` (16.57 m) exceeds 10 m, `10 − displacement_height` would be negative and the log-profile undefined. Instead, a two-stage log-profile extrapolation is used:
      1. 10 m (open terrain) → `blending_height` (60 m), using open-terrain parameters only (`roughness_length_freifeld`, no displacement height).
      2. `blending_height` → hub height, carried out by windpowerlib's own logarithmic wind profile, using the local urban `roughness_length` and `obstacle_height`.
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

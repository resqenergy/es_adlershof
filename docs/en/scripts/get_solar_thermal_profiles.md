# Compute solar thermal profiles

## Purpose

Computes hourly heat output profiles of a flat-plate collector for all available TRY weather datasets. The normalized profiles serve as feed-in profiles for solar thermal installations in the energy system model.

## Inputs

| Path | Description |
|------|--------------|
| `<npro_weather_dir>/*.csv` | TRY weather data (hourly values, semicolon-separated) with columns `radiation_downwelling`, `radiation_diffuse`, `air_temperature_mean` |

The weather folder is determined via `npro.settings.WEATHER_DIR`.

## Outputs

| Path | Description |
|------|--------------|
| `datasets/solar_thermal_profiles/solar_thermal_profile_<weatherfile>.csv` | Hourly collector heat output \[W/m²\], column `solar_thermal_power`, index `timeindex` |

One output file is created per TRY weather file. The period marker (`p1`, `p2`, `p3`) in the file name determines the target year (2025, 2035, 2050).

## Parameters

All parameters are defined directly as constants in the script:

| Parameter | Value | Description |
|-----------|------|--------------|
| `ETA_0` | 0.718 | Optical efficiency of the collector |
| `A1` | 3.89 | First-order thermal loss coefficient \[W/(m²·K)\] |
| `A2` | 0.018 | Second-order thermal loss coefficient \[W/(m²·K²)\] |
| `TILT` | 0° | Collector tilt angle |
| `AZIMUT` | 20° | Azimuth angle (east of north) |
| `TEMP_INLET` | 50 °C | Collector inlet temperature |
| `LAT` | 52.43° | Latitude (Adlershof, Berlin) |
| `LONG` | 13.54° | Longitude (Adlershof, Berlin) |

Collector characteristics come from the data sheet of a standard flat-plate collector (source: duurzaamloket.nl).

## Algorithm

1. For each TRY weather file in the NPRO weather folder:
   - Extract the period marker (`p1`/`p2`/`p3`) from the file name → determine target year
   - Read weather data: global irradiance, diffuse irradiance, air temperature
   - Build the time index as an hourly DatetimeIndex series for the target year
2. Compute the collector irradiance on the tilted surface via pvlib:
   - Compute the sun position (`pvlib.solarposition.get_solarposition`)
   - Derive direct normal irradiance (DNI) from GHI and DHI
   - Compute total irradiance on the collector (`poa_global`)
3. Collector efficiency per EN 12975:
   - `η = η₀ − a₁·ΔT/E − a₂·ΔT²/E`
   - `ΔT = T_inlet + ΔT_n − T_amb`
   - Efficiency is clipped at 0 (no negative yield)
4. Heat output: `Q = η · E_coll`
5. Save result as CSV

## Dependencies

**pvlib** (`pvlib>=0.15.1`): computes sun position, direct normal irradiance, and total irradiance on the collector surface. Replaces manual geometric calculations.

**npro**: provides the path to the weather folder (`npro.settings.WEATHER_DIR`), which contains the TRY input data.

## Execution

```bash
make solar_thermal
```

Equivalent to: `uv run -m scripts.get_solar_thermal_profiles`

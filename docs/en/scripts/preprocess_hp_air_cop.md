# COP time series for air heat pumps

## Purpose

Computes an hourly COP time series for air heat pumps based on outdoor air temperatures and a constant supply temperature. The COP is determined using the Carnot approach with a fixed quality grade.

## Inputs

| Path | Description |
|------|--------------|
| `raw/weather/weatherdata_<region>_<year>.csv` | Hourly weather data with column `temp_air` (outdoor air temperature in °C) |

Default: region `AD` (Adlershof), year `2050`.

## Outputs

| Path | Description |
|------|--------------|
| `datasets/heatpump_air/ts_hp_air_cop.csv` | Hourly COP time series, column `heatpump_air-profile`, index `timeindex`, semicolon-separated |

## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `DEFAULT_REGION` | `"AD"` | Region code for the weather file |
| `DEFAULT_YEAR` | `2050` | Reference year |
| `DEFAULT_TEMP_HIGH` | `50.0 °C` | Supply temperature (condenser side) |
| `QUALITY_GRADE` | `0.4` | Quality grade η (ratio of real to Carnot COP) |
| `TEMPERATURE_LOW_COLUMN` | `"temp_air"` | Column name in the weather file |

## Algorithm

1. Read outdoor air temperature from the weather file (`temp_air` in °C)
2. Create the supply temperature as a constant time series (50 °C)
3. Compute COP using the Carnot formula with quality grade:

$$\text{COP} = \frac{T_\text{high}}{T_\text{high} - T_\text{low}} \cdot \eta$$

   with temperatures in Kelvin (°C + 273.15)
4. Build the time index as an hourly DatetimeIndex series for the target year
5. Save result as a semicolon-separated CSV

## Dependencies

No external libraries beyond the project standard (pandas, pathlib).

## Execution

```bash
uv run -m scripts.preprocess_hp_air_cop
```

No standalone Makefile target. Required as a preprocessing step before `preprocess_hp_air_cost.py`.

# Precompute normalized PV feed-in time series (GSEE)

## Purpose

Uses GSEE (Global Solar Energy Estimator) to compute normalized hourly PV feed-in time series — one per mounting orientation (tilt/azimuth combination) — from TRY weather data. Output is dimensionless (W fed in per W installed) and serves as the raw material for `calc_pv_timeseries.py`, which later combines these per-orientation profiles into per-technology (`pv_roof`, `pv_facade`) profiles using the area-share weights in `raw/pv_config/pv_config.csv`.

> **Note:** This is a one-off precompute step. Normalized GSEE feed-in profiles have already been generated for all weather scenarios currently used in this project. You only need to (re-)run this script if a new weather scenario is added — otherwise `calc_pv_timeseries.py` can be run directly against the existing files in `datasets/gsee_timeseries/`.

## Inputs

| Path | Description |
|------|--------------|
| `raw/weather/*.csv` | TRY weather data (semicolon-separated), same files used by `calc_wind_timeseries.py` and `get_solar_thermal_profiles.py`. Columns used: `radiation_downwelling`, `radiation_diffuse`, `air_temperature_mean` |

The calendar year is derived from the file name:

| File name marker | Calendar year |
|-------------------|-------------|
| `p1` | 2020 |
| `p2` | 2035 |
| `p3` | 2050 |
| `reference` | 2011 (own assumption of a historical reference year) |

Alternatively, a year can be provided manually via `args["year"]` — but not in combination with a file name containing a period marker (raises `ValueError` if both are given, or if neither is given).

## Outputs

**Path:** `datasets/gsee_timeseries/gsee_timeseries-{filename}-{year}.csv`

One CSV file is generated per TRY weather file, indexed by `timeindex`, with one column per `(tilt, azimuth)` combination (MultiIndex columns). Values are the normalized PV feed-in (dimensionless, W fed in per W installed).

## Parameters

The parameters are defined in the `args` dict at the top of the script:

| Parameter | Value | Description |
|-----------|------|-------------|
| `year` | `None` | Manual override for the calendar year; leave `None` to resolve it from the file name |
| `periods` | `8760` | Hours per year |
| `coords` | `(52.43, 13.54)` | Coordinates of Adlershof (Berlin) |
| `tilt` | `[30, 90]` | Tilt angles in degrees — 30° for roof-mounted, 90° for facade-mounted PV |
| `azimut` | `[90, 135, 180, 225, 270]` | Azimuth angles in degrees (E, SE, S, SW, W) |
| `capacity` | `1` | Installed capacity passed to GSEE; kept at 1 (dimensionless W/W) so the output is a normalized feed-in fraction rather than an absolute power |

## Algorithm

1. **Resolve year** (`resolve_year`) — determine the calendar year either from `args["year"]` or from the `p1`/`p2`/`p3`/`reference` marker in the weather file name.
2. **Read and prepare weather data** (`read_and_prepare_weatherdata`):
   - Select `radiation_downwelling`, `radiation_diffuse`, `air_temperature_mean` and rename to `global_horizontal`, `diffuse_fraction` (derived), `temperature`.
   - Build an hourly `DatetimeIndex` starting Jan 1 of the resolved year.
   - Compute `diffuse_fraction = radiation_diffuse / global_horizontal`, clipped to ≥ 0 and forced to 0 where `global_horizontal == 0`.
   - Validation: if more than 5% of rows have negative `radiation_diffuse`, the function is intended to raise a `ValueError` recommending a manual check of the TRY file.
     > **Known issue:** the current implementation uses Python 2-style tuple-raise syntax (`raise (ValueError, "...")`), which does not raise a `ValueError` in Python 3 — it raises an unrelated `TypeError` instead. The validation message is never actually shown. Tracked for a fix; not addressed as part of this documentation pass.
3. **Run GSEE** (`run_gsee`) — for every combination of `tilt` (2 values) and `azimut` (5 values), calls `gsee.pv.run_model(..., tracking=0, capacity=1)` (`tracking=0`: fixed-mount, no solar tracking) and collects the 10 resulting series into one DataFrame with `(tilt, azimut)` MultiIndex columns.
4. **Save** — one output CSV per input weather file.

## Dependencies

**gsee** (`gsee.pv.run_model`) — the PV simulation core. The `gsee` package (0.3.1) is unmaintained upstream and only supports very old `numpy`/`pandas`/`pvlib-python` versions, so it must be run in a dedicated legacy conda environment (`gsee37`, Python 3.7.12) rather than the project's normal `uv` environment — see `scripts/pv_precalc/environment.yaml`.

## Execution

No standalone `uv` invocation — this script requires the `gsee37` conda environment:

```bash
$(conda info --base)/envs/gsee37/bin/python scripts/pv_precalc/calc_gsee_timeseries.py
```

Makefile target:

```bash
make gsee_timeseries
```

which resolves `GSEE_PYTHON` to the `gsee37` environment's Python interpreter. As noted above, this is a precompute step already run for all currently used weather scenarios — only re-run it when adding a new weather scenario.

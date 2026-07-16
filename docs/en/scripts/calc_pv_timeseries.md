# Combine PV feed-in time series into technology profiles

## Purpose

Combines the normalized per-orientation PV feed-in time series produced by `calc_gsee_timeseries.py` into one time series per PV technology (`pv_roof`, `pv_facade`), weighted by each orientation's share of installed PV area. Serves as the feed-in profile source for the PV roof and facade models in the energy system model.

## Inputs

| Path | Description |
|------|--------------|
| `raw/pv_config/pv_config.csv` | PV area-share configuration. Columns: `technology` (`pv_roof`, `pv_facade`), `tilt` (mounting tilt angle in degrees), `azimuth` (mounting azimuth angle in degrees), `weight` (share of that technology's installed PV area at this tilt/azimuth). `weight` sums to 1 per technology, across all its tilt/azimuth rows |
| `datasets/gsee_timeseries/*gsee_timeseries*.csv` | Normalized per-`(tilt, azimuth)` PV feed-in time series, produced by `calc_gsee_timeseries.py` |

> **Note:** every `(tilt, azimuth)` pair referenced in `pv_config.csv` must exist as a column in the GSEE timeseries file, i.e. it must be covered by `calc_gsee_timeseries.py`'s `args["tilt"]` / `args["azimut"]` (currently `tilt=[30, 90]`, `azimut=[90, 135, 180, 225, 270]`). Adding a new tilt or azimuth to `pv_config.csv` without regenerating the GSEE timeseries for it will raise a `KeyError`.

## Outputs

**Path:** `datasets/pv_profiles/pv_timeseries-{name}-{year}.csv`

One CSV file is generated per input GSEE timeseries file, indexed by `timeindex`, with one column per technology (`pv_roof`, `pv_facade`).

## Parameters

Defined as path constants at the top of the script:

| Parameter | Value | Description |
|-----------|------|--------------|
| `PV_CONFIG_FILE` | `raw/pv_config/pv_config.csv` | PV area-share configuration |
| `GSEE_TIMESERIES_DIR` | `datasets/gsee_timeseries` | Input directory, scanned for files containing `"gsee_timeseries"` in their name |
| `RESULTS_DIR` | `datasets/pv_profiles` | Output directory |

## Algorithm

1. **`calc_pv_feedin(gsee_timeseries_file)`**:
   - Load `pv_config.csv` and the given GSEE timeseries file (MultiIndex columns `(tilt, azimuth)`, numeric levels).
   - Group `pv_config` rows by `technology`. For each technology, sum `gsee_timeseries[(tilt, azimuth)] * weight` across **all** rows in the group — this already supports a technology having several distinct tilt angles, not just the current one-tilt-per-technology setup (`pv_roof` = 30°, `pv_facade` = 90°).
   - One resulting column per technology.
2. **Main loop** — for every file in `GSEE_TIMESERIES_DIR` whose name contains `"gsee_timeseries"`: run `calc_pv_feedin`, derive the output file name from the input file name (`gsee_timeseries-{name}-{year}.csv` → `pv_timeseries-{name}-{year}.csv`), and save to `RESULTS_DIR`.

## Dependencies

No external libraries beyond the project standard (pandas).

## Execution

```bash
make pv_timeseries
```

Equivalent to: `uv run -m scripts.calc_pv_timeseries`

Runs in the project's normal `uv` environment — unlike `calc_gsee_timeseries.py`, it does not need the `gsee37` conda environment. The Makefile's `all` target runs `gsee_timeseries` before `pv_timeseries`, but in practice this script can simply be run against the already-precomputed files in `datasets/gsee_timeseries/` (see [calc_gsee_timeseries.py docs](calc_gsee_timeseries.md)) without re-running the GSEE step.

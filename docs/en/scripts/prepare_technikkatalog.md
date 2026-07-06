# Prepare technology catalog

## Purpose

Filters and renames technology parameters from the KWW technology catalog so they can be read by oemof-pipe as component parameters. Produces a cleaned CSV with cost and efficiency values for the heat supply technologies used in the model.

## Inputs

| Path | Description |
|------|--------------|
| `raw/technikkatalog/KWW-Technikkatalog-Waermeplanung_12-2025(flatdata_all).csv` | Flat-data export of the technology catalog (last sheet `flatdata_all`), semicolon-separated |

The input path is defined in `utils/technikkatalog.py` as `FLATDATA_FILE_RAW`.

## Outputs

| Path | Description |
|------|--------------|
| `datasets/technology_cost/kww_technikkatalog.csv` | Filtered and renamed technology parameters, semicolon-separated, for oemof-pipe |

## Parameters

The mapping of technology catalog entries to model components is defined in the script as `TECHNOLOGY_MAPPING`:

| Technology catalog designation | Capacity \[MW\] | Model name |
|---------------------------|----------------|------------|
| `AbwaermeWP_zentral` | 2 | `heatpump_office` |
| `AbwaermeWP_zentral` | 10 | `heatpump_nt` |
| `AbwaermeWP_zentral` | 20 | `heatpump_mt` |
| `BHKW_zentral` | 0.3 | `bhkw` |
| `Tiefengeothermie_ab400_direkt_zentral` | 10 | `heatpump_geothermal` |
| `AbwasserWP_zentral` | 10 | `heatpump_wastewater` |
| `GewaesserWP_zentral` | 10 | `heatpump_canal` |
| `Solarthermie_flach_dezentral` | 10 | `heat_decentral-solarthermal` |

For new technologies: extend `TECHNOLOGY_MAPPING`, then re-run the script.

## Algorithm

1. Call `get_technology_data(TECHNOLOGY_MAPPING)` from `utils/technikkatalog.py`
2. The function reads the raw data and filters by the specified technologies and capacities
3. Columns and technology names are renamed to oemof-pipe-compliant designations according to the mapping
4. Result is saved as a semicolon-separated CSV

The script contains no processing logic of its own — all filtering and renaming lives in `utils/technikkatalog.py`.

## Dependencies

No external libraries beyond the project standard. Internal dependency: `utils.technikkatalog` (contains `Technology`, `get_technology_data`, `FLATDATA_FILE_RAW`).

**oemof-pipe**: consumes the output file as a technology parameter source for blueprints.

## Execution

```bash
make parameters
```

Equivalent to (first step): `uv run -m scripts.prepare_technikkatalog`

!!! note "Prerequisite"
    The last sheet (`flatdata_all`) of the Excel technology catalog must be manually exported as CSV beforehand and placed under `raw/technikkatalog/`.

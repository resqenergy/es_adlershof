# Merge building areas

## Purpose

Merges the cluster CSVs for companies and residents and computes the total usable floor area and usage units per building cluster for the three district heating supply topologies `central`, `low_temp_central`, and `decentral`.

## Inputs

| Path | Content |
|------|--------|
| `raw/cluster/companies_area_and_units_per_cluster_central.csv` | Usable floor area and units of company buildings (central) |
| `raw/cluster/companies_area_and_units_per_cluster_decentral.csv` | Usable floor area and units of company buildings (decentral) |
| `raw/cluster/residents_area_and_units_per_cluster_central.csv` | Usable floor area and units of residential buildings (central) |
| `raw/cluster/residents_area_and_units_per_cluster_low_temp_central.csv` | Usable floor area and units of residential buildings (low-temperature network) |
| `raw/cluster/residents_area_and_units_per_cluster_decentral.csv` | Usable floor area and units of residential buildings (decentral) |

All input files share the same structure:

| Column | Description |
|--------|-------------|
| `Cluster` | Building type designation (e.g. "office", "multi-family house") |
| `Nutzfläche_m2_statusquo` | Usable floor area in the status quo \[m²\] |
| `Nutzeinheiten_statusquo` | Number of usage units in the status quo |

## Outputs

All output files end up in `datasets/areas/` and have the same structure as the inputs:

| File | Content |
|-------|--------|
| `datasets/areas/total_area_and_units_central.csv` | Sum of companies + residents (central) |
| `datasets/areas/total_area_and_units_low_temp_central.csv` | Residents only (low-temperature network) |
| `datasets/areas/total_area_and_units_decentral.csv` | Sum of companies + residents (decentral) |

## Parameters

No configurable parameters. Paths are hardcoded in the script.

## Algorithm

1. Loads the company and resident CSVs per topology.
2. For `central` and `decentral`, merges the datasets via `pd.concat` and sums all numeric columns per `Cluster` using `groupby`.
3. For `low_temp_central`, only the resident data is used (no company buildings in this network).
4. Saves the three merged DataFrames as CSV.
5. Writes a metadata file via `utils.metadata.write_metadata`.

## Dependencies

- **pandas** — reading, merging, and saving data.

## Execution

```bash
make areas
```

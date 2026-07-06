# Area forecast by usage type

## Purpose

Projects usable floor area and usage units per building cluster onto the planning horizons 2035 and 2050, based on growth factors derived from the zoning plan. For 2050, an additional reallocation effect is modeled: buildings of construction age class 1995–2001 are fully shifted to the "2002 and later" class.

## Inputs

| Path | Content |
|------|--------|
| `datasets/areas/total_area_and_units_central.csv` | Merged areas (central, status quo) |
| `datasets/areas/total_area_and_units_low_temp_central.csv` | Merged areas (low temperature, status quo) |
| `datasets/areas/total_area_and_units_decentral.csv` | Merged areas (decentral, status quo) |

## Outputs

All output files end up in `datasets/areas_forecast/`:

| File | Content |
|-------|--------|
| `total_area_and_units_central_with_forecast.csv` | Area forecast for central supply |
| `total_area_and_units_low_temp_central_with_forecast.csv` | Area forecast for low-temperature network |
| `total_area_and_units_decentral_with_forecast.csv` | Area forecast for decentral supply |

Each output file contains additional columns compared to the inputs:

| Column | Description |
|--------|-------------|
| `Übercluster` | Super-category of the cluster (e.g. "commercial", "residential") |
| `Nutzfläche_m2_2035` | Projected usable floor area for 2035 \[m²\] |
| `Nutzeinheiten_2035` | Projected usage units for 2035 |
| `Nutzfläche_m2_2050` | Projected usable floor area for 2050 \[m²\] |
| `Nutzeinheiten_2050` | Projected usage units for 2050 |

## Parameters

The growth parameters are hardcoded directly in the script:

| Parameter | Value | Meaning |
|-----------|------|-----------|
| Growth share 2035 | 25 % of total growth | `Nutzfläche_statusquo * (1 + 0.25 * wachstum_rel)` |
| Growth share 2050 | 60 % of total growth | `Nutzfläche_statusquo * (1 + 0.60 * wachstum_rel)` |

Base zoning plan data (hardcoded):

| Super-cluster | Available area \[m²\] | Built area \[m²\] |
|-------------|------------------------|----------------------|
| Commercial | 5,122,822 | 1,314,408 |
| Residential | 282,444 | 280,418 |
| Media | 177,007 | 135,080 |
| Research | 288,891 | 139,109 |
| University | 138,247 | 91,198 |

## Algorithm

1. Loads the three area CSVs from `datasets/areas/`.
2. Computes the relative growth factor per super-cluster: `available / built - 1`.
3. Assigns each cluster to a super-cluster via the `cluster_to_super` mapping.
4. Computes the projected areas for 2035 (25 % of growth potential) and 2050 (60 % of growth potential).
5. Performs a reallocation for 2050: the area and units of single-family houses in the 1995–2001 construction age class are added to the "2002 and later" class, since these buildings will have been modernized or replaced by 2050. The values of the old class are set to 0.
6. Saves the three projected DataFrames as CSV in `datasets/areas_forecast/`.

## Dependencies

- **pandas** — loading, transforming, and saving data.

## Execution

```bash
make areas_forecast
```

Requires `make areas` as a preceding step.

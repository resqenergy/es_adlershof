# Generate hourly waste-heat profiles

## Purpose

Disaggregates annual waste-heat potentials into hourly profiles per temperature level (HT/MT/NT/office). The time profiles are derived from demand-side heat and cooling profiles as well as source-specific availability windows, then scaled to scenario-dependent annual energy totals.

## Inputs

| Path | Description |
|------|-------------|
| `raw/wasteheat_potentials/Abwaermepotenzial_Adlershof_BfEE.csv` | Waste-heat sources with temperature ranges, monthly power profiles, and availability per source |
| `raw/wasteheat_potentials/Abwärmepotenziale_Adlershof.xlsx` | Annual energy totals per technology and planning horizon (2025/2035/2050) in MWh |
| `datasets/demand_profiles/{scenario}.csv` | Normalized hourly demand profiles (heat, cooling) for the selected scenario |

## Outputs

**Path:** `datasets/wasteheat_profiles/{scenario}.csv`

| Column | Description |
|--------|-------------|
| `timeindex` | Hourly timestamp |
| `heatpump_ht-low_temperature_potential` | High-temperature waste heat (≥90 °C) \[kWh/h\] |
| `heatpump_mt-low_temperature_potential` | Medium-temperature waste heat (60–90 °C) \[kWh/h\] |
| `heatpump_nt-low_temperature_potential` | Low-temperature waste heat (<60 °C) \[kWh/h\] |
| `heatpump_office-low_temperature_potential` | Laundry/office/lab waste heat \[kWh/h\] |

## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `SCENARIO` | e.g. `2035_mean_rcp85` | Climate scenario (command-line argument) |
| `YEAR` | e.g. `2035` | Planning horizon for annual energy totals (2025/2035/2050) |
| `YEAR_INDEX_LOOKUP` | `{2025: 0, 2035: 1, 2050: 2}` | Column index in the Excel energy potential sheet |

**Temperature level classification:**

| Temperature range | Level |
|-------------------|--------|
| ≥90 °C, 90–110 °C | HT |
| 60–90 °C | MT |
| otherwise | NT |

**Source-specific availability windows** (excerpt):

| Source | Hours |
|--------|---------|
| Refrigeration plant, NSHV, compressed air, … | 0–24 h |
| iKWK module | 6–17 h |
| Glass module, KKM, RLT | 8–16 h |
| Cooling BFS 360 | 6–18 h |

## Algorithm

1. **Load raw data** — the BfEE CSV of waste-heat sources and the Excel file with annual energy totals are read and classified into temperature levels.
2. **Build time index** — an 8760-hour DatetimeIndex for the selected year is created (month, hour, weekday).
3. **Demand-based base profiles** — normalized central heat and cooling profiles are derived from the scenario's demand profile: HT/MT use the heat profile, NT the cooling profile.
4. **Compute source profiles** — for each waste-heat source:
   - Compute monthly weights from the power profile.
   - Build an availability mask from the daily window and weekend flag.
   - Per month: base profile × availability × monthly weight → hourly energy.
5. **Aggregate** — sum profiles of all sources per temperature level.
6. **Scale to annual energy totals** — aggregated profiles are normalized and scaled to the scenario-dependent annual energy totals from the Excel file.
7. **Save** — output as CSV with `timeindex` and four power columns.

## Dependencies

**pandas / numpy** — data processing, time series operations, vectorization of profile generation.

## Execution

```bash
make wasteheat_profiles SCENARIO=2035_mean_rcp85 YEAR=2035
```

Scenario and year are adjustable. The target requires `demand_profiles`.

# Scripts – Overview

This page gives a short overview of all data-pipeline processing scripts. They are organized into three groups: scripts that determine **energy demand**, scripts for **energy supply** (renewable generation and waste heat), and scripts for **techno-economic parameters** (cost and technology data). Each row links to the detailed documentation of the respective script.

## Energy demand

| Name | Script name (.py) | Description |
|------|--------------------|--------------|
| [Merge building areas](get_total_area_and_units.md) | `get_total_area_and_units.py` | Merges company and resident cluster data and computes usable floor area and usage units per building cluster and supply topology. |
| [Area forecast](get_area_per_type_of_use_projection.md) | `get_area_per_type_of_use_projection.py` | Projects floor area and usage units per cluster onto the 2035/2050 planning horizons using growth factors from the zoning plan. |
| [NPRO building simulations](get_demands_per_building.md) | `get_demands_per_building.py` | Creates NPRO scenario YAMLs for all combinations of climate scenario, planning horizon, and topology to compute hourly building demand profiles. |
| [Aggregate demand profiles](get_demand_profiles.md) | `get_demand_profiles.py` | Aggregates the hourly NPRO demand profiles per scenario and topology into normalized hourly profiles and annual totals. |

## Energy supply: renewables & waste heat

| Name | Script name (.py) | Description |
|------|--------------------|--------------|
| [Precompute PV time series (GSEE)](calc_gsee_timeseries.md) | `scripts/pv_precalc/calc_gsee_timeseries.py` | Uses GSEE to compute normalized hourly PV feed-in time series per mounting orientation from TRY weather data. |
| [Combine PV time series into tech profiles](calc_pv_timeseries.md) | `calc_pv_timeseries.py` | Combines the GSEE per-orientation profiles, area-weighted, into one time series per PV technology (roof/facade). |
| [Wind power time series](calc_wind_timeseries.md) | `calc_wind_timeseries.py` | Computes normalized hourly wind power time series from TRY weather data for each climate path. |
| [Solar thermal profiles](get_solar_thermal_profiles.md) | `get_solar_thermal_profiles.py` | Computes hourly heat output profiles of a flat-plate collector for all TRY weather datasets. |
| [Hourly waste-heat profiles](get_waste_heat_profiles.md) | `get_waste_heat_profiles.py` | Disaggregates annual waste-heat potentials into hourly profiles per temperature level. |
| [COP waste-heat heat pumps](calc_heat_waste_cop.md) | `calc_heat_waste_cop.py` | Computes hourly COP time series for six waste-heat heat pump components from their source temperatures. |
| [Waste-heat capacities](calc_heat_waste_power.md) | `calc_heat_waste_power.py` | Derives thermal capacity potentials for all waste-heat heat pump components. |
| [Teltow Canal heat quantity](calc_waermemenge_teltowkanal.md) | `calc_waermemenge_teltowkanal.py` | Estimates the mean usable heat output of the Teltow Canal as a heat pump source from flow and temperature data. |
| [COP air heat pumps](preprocess_hp_air_cop.md) | `preprocess_hp_air_cop.py` | Computes an hourly COP time series for air heat pumps using the Carnot approach. |

## Techno-economic parameters

| Name | Script name (.py) | Description |
|------|--------------------|--------------|
| [Prepare technology catalog](prepare_technikkatalog.md) | `prepare_technikkatalog.py` | Filters and renames technology parameters from the KWW technology catalog for use in oemof-pipe. |
| [Capacity costs](preprocess_capacity_costs.md) | `preprocess_capacity_costs.py` | Computes annualized capacity costs from CAPEX, lifetime, WACC, and operating costs for heat technologies and solar thermal. |
| [Costs air heat pumps](preprocess_hp_air_cost.md) | `preprocess_hp_air_cost.py` | Determines capacities and weighted mean costs for decentral air heat pumps per scenario. |

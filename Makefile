
SCENARIO ?= 2050_mean_rcp85
YEAR ?= 2050
STARTTIME ?= "$(YEAR)-01-01 00:00:00"
GSEE_PYTHON := $(shell conda info --base)/envs/gsee37/bin/python

all: areas areas_forecast npro_scenarios npro_buildings demand_profiles wasteheat_profiles wasteheat_cops wasteheat_capacities solar_thermal gsee_timeseries pv_timeseries bev_timeseries parameters datapackage

areas:
	uv run -m scripts.get_total_area_and_units

areas_forecast:
	uv run -m scripts.get_area_per_type_of_use_projection

npro_scenarios:
	uv run -m scripts.get_demands_per_building

npro_buildings:
	uv run npro run all

demand_profiles:
	uv run -m scripts.get_demand_profiles

wasteheat_profiles:
	uv run -m scripts.get_waste_heat_profiles $(SCENARIO) $(YEAR)

wasteheat_cops:
	uv run -m scripts.calc_heat_waste_cop $(YEAR)

wasteheat_capacities:
	uv run -m scripts.calc_heat_waste_power $(SCENARIO) $(YEAR)

solar_thermal:
	uv run -m scripts.get_solar_thermal_profiles

gsee_timeseries:
	$(GSEE_PYTHON) scripts/pv_precalc/calc_gsee_timeseries.py

pv_timeseries:
	uv run -m scripts.calc_pv_timeseries

bev_timeseries:
	uv run -m scripts.get_bev_charging_profiles

wind_timeseries:
	uv run -m scripts.calc_wind_timeseries

parameters:
	uv run -m scripts.prepare_technikkatalog
	uv run -m scripts.prepare_technologies
	uv run -m scripts.preprocess_capacity_costs

datapackage:
	uv run oemof-pipe blueprint -f adlershof --start $(STARTTIME) --periods 8760
	uv run oemof-pipe scenario -f adlershof $(SCENARIO)

export_datapackage:
	uv run -m utils.export_to_s3 adlershof_$(SCENARIO)

docs:
	uv run zensical build
	uv run zensical build -f zensical.en.toml

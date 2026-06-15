
SCENARIO ?= 2035_mean_rcp85
YEAR ?= 2035

all: wasteheat_profiles wasteheat_cops areas_forecast parameters datapackage

areas:
	uv run -m scripts.get_total_area_and_units

areas_forecast: areas
	uv run -m scripts.get_area_per_type_of_use_projection

npro_scenarios: areas_forecast
	uv run -m scripts.get_demands_per_building

npro_buildings: npro_scenarios
	uv run npro run all

demand_profiles: npro_buildings
	uv run -m scripts.get_demand_profiles

wasteheat_profiles: demand_profiles
	uv run -m scripts.get_waste_heat_profiles $(SCENARIO) $(YEAR)

wasteheat_cops:
	uv run -m scripts.calc_heat_waste_cop $(YEAR)

wasteheat_capacities:
	uv run -m scripts.calc_heat_waste_power

solar_thermal:
	uv run -m scripts.get_solar_thermal_profiles

parameters:
	uv run -m scripts.prepare_technikkatalog
	uv run -m scripts.preprocess_capacity_costs

datapackage:
	uv run oemof-pipe blueprint -f adlershof
	uv run oemof-pipe scenario -f adlershof $(SCENARIO)

export_datapackage:
	uv run -m utils.export_to_s3 adlershof_$(SCENARIO)

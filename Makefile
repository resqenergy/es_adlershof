
SCENARIO ?= 2050_mean_rcp85
YEAR ?= 2050
STARTTIME ?= "$(YEAR)-01-01 00:00:00"
GSEE_PYTHON := $(shell conda info --base)/envs/gsee37/bin/python

# Targets are completion markers: each script writes its metadata file last,
# so an existing marker means the dataset is complete and the step is skipped.
# Folder targets (npro_buildings, datapackages) are checked for existence only.
# See docs/adr/0001-make-targets-skip-existing.md.
AREAS := datasets/areas/metadata.json
AREAS_FORECAST := datasets/areas_forecast/metadata.json
NPRO_SCENARIOS := datasets/npro_scenarios/metadata.json
NPRO_BUILDINGS := datasets/npro_buildings
DEMAND_PROFILES := datasets/demand_profiles/metadata.json
WASTEHEAT_PROFILES := datasets/wasteheat_profiles/$(SCENARIO).metadata.json
WASTEHEAT_COPS := datasets/wasteheat_cop/cop_$(YEAR).metadata.json
WASTEHEAT_CAPACITIES := datasets/wasteheat_capacity/capacity_$(SCENARIO).metadata.json
SOLAR_THERMAL := datasets/solar_thermal_profiles/metadata.json
GSEE_TIMESERIES := datasets/gsee_timeseries/metadata.json
PV_TIMESERIES := datasets/pv_profiles/metadata.json
BEV_TIMESERIES := datasets/bev_charging_profiles/metadata.json
WIND_TIMESERIES := datasets/wind_profiles/metadata.json
TECHNIKKATALOG := datasets/technology_cost/metadata.json
TECHNOLOGIES := datasets/technology_data/metadata.json
# preprocess_capacity_costs writes technology_capacity_cost/ and solar_thermal/; solar_thermal metadata is written last.
CAPACITY_COSTS := datasets/solar_thermal/metadata.json
BLUEPRINT := datapackages/adlershof_$(YEAR)
DATAPACKAGE := datapackages/adlershof_$(SCENARIO)

DATASETS := $(AREAS) $(AREAS_FORECAST) $(NPRO_SCENARIOS) $(NPRO_BUILDINGS) $(DEMAND_PROFILES) \
	$(WASTEHEAT_PROFILES) $(WASTEHEAT_COPS) $(WASTEHEAT_CAPACITIES) $(SOLAR_THERMAL) \
	$(GSEE_TIMESERIES) $(PV_TIMESERIES) $(BEV_TIMESERIES) $(WIND_TIMESERIES) \
	$(TECHNIKKATALOG) $(TECHNOLOGIES) $(CAPACITY_COSTS)

.PHONY: all areas areas_forecast npro_scenarios npro_buildings demand_profiles wasteheat_profiles wasteheat_cops wasteheat_capacities solar_thermal gsee_timeseries pv_timeseries bev_timeseries wind_timeseries parameters datapackage export_datapackage docs

all: areas areas_forecast npro_scenarios npro_buildings demand_profiles wasteheat_profiles wasteheat_cops wasteheat_capacities solar_thermal gsee_timeseries pv_timeseries bev_timeseries wind_timeseries parameters datapackage

areas: $(AREAS)
$(AREAS):
	uv run -m scripts.get_total_area_and_units

areas_forecast: $(AREAS_FORECAST)
$(AREAS_FORECAST): $(AREAS)
	uv run -m scripts.get_area_per_type_of_use_projection

npro_scenarios: $(NPRO_SCENARIOS)
$(NPRO_SCENARIOS): $(AREAS_FORECAST)
	uv run -m scripts.get_demands_per_building

npro_buildings: | $(NPRO_BUILDINGS)
$(NPRO_BUILDINGS): | $(NPRO_SCENARIOS)
	uv run npro run all

demand_profiles: $(DEMAND_PROFILES)
$(DEMAND_PROFILES): | $(NPRO_BUILDINGS)
	uv run -m scripts.get_demand_profiles

wasteheat_profiles: $(WASTEHEAT_PROFILES)
$(WASTEHEAT_PROFILES): $(DEMAND_PROFILES)
	uv run -m scripts.get_waste_heat_profiles $(SCENARIO) $(YEAR)

wasteheat_cops: $(WASTEHEAT_COPS)
$(WASTEHEAT_COPS):
	uv run -m scripts.calc_heat_waste_cop $(YEAR)

wasteheat_capacities: $(WASTEHEAT_CAPACITIES)
$(WASTEHEAT_CAPACITIES): $(WASTEHEAT_COPS) $(WASTEHEAT_PROFILES)
	uv run -m scripts.calc_heat_waste_power $(SCENARIO) $(YEAR)

solar_thermal: $(SOLAR_THERMAL)
$(SOLAR_THERMAL):
	uv run -m scripts.get_solar_thermal_profiles

gsee_timeseries: $(GSEE_TIMESERIES)
$(GSEE_TIMESERIES):
	$(GSEE_PYTHON) scripts/pv_precalc/calc_gsee_timeseries.py

pv_timeseries: $(PV_TIMESERIES)
$(PV_TIMESERIES): $(GSEE_TIMESERIES)
	uv run -m scripts.calc_pv_timeseries

bev_timeseries: $(BEV_TIMESERIES)
$(BEV_TIMESERIES):
	uv run -m scripts.get_bev_charging_profiles

wind_timeseries: $(WIND_TIMESERIES)
$(WIND_TIMESERIES):
	uv run -m scripts.calc_wind_timeseries

parameters: $(TECHNIKKATALOG) $(TECHNOLOGIES) $(CAPACITY_COSTS)
$(TECHNIKKATALOG):
	uv run -m scripts.prepare_technikkatalog

$(TECHNOLOGIES):
	uv run -m scripts.prepare_technologies

$(CAPACITY_COSTS): $(TECHNIKKATALOG) $(TECHNOLOGIES)
	uv run -m scripts.preprocess_capacity_costs

datapackage: | $(DATAPACKAGE)
# oemof-pipe's -f checks the blueprint/scenario name, not --target, so clear the target ourselves.
$(BLUEPRINT):
	rm -rf $@
	uv run oemof-pipe blueprint -f adlershof --start $(STARTTIME) --periods 8760 --target adlershof_$(YEAR)

$(DATAPACKAGE): | $(BLUEPRINT) $(DATASETS)
	rm -rf $@
	uv run oemof-pipe scenario -f adlershof_$(YEAR) --target adlershof_$(SCENARIO) $(SCENARIO)

export_datapackage:
	uv run -m utils.export_to_s3 adlershof_$(SCENARIO)

docs:
	uv run zensical build
	uv run zensical build -f zensical.en.toml

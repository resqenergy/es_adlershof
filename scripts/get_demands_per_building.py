"""Module to create and run NPRO scenarios based on area and unit distribution per building type."""

from __future__ import annotations

import math
from typing import Any

import yaml
from npro.settings import SCENARIOS_DIR, WEATHER_DIR
from utils.files import read_file, write_file
from settings import RESULTS_DIR, CONFIG_DIR

BUILDING_SHARES_PATH = CONFIG_DIR / "building_shares.yaml"

YEAR_ORDER = ("statusquo", "2035", "2050")


def get_building_shares() -> dict[str, dict[str, float]]:
    """Read building_shares.yaml and return shares per year."""
    with BUILDING_SHARES_PATH.open("r") as f:
        shares = yaml.safe_load(f)
    for year in shares:
        if shares[year]["existing"] + shares[year]["new"] != 1.0:
            raise ValueError(f"Share for year '{year}' does not sum up to 1.0.")
    return shares


def get_npro_buildings(
    distribution_name: str, year: str, topology: str
) -> dict[str, dict[str, Any]]:
    """Create buildings for NPRO scenario based on distribution and year."""

    def get_area_and_units_for_year(selected_year: str) -> tuple[float, int]:
        return (
            row[f"Nutzfläche_m2_{selected_year}"],
            row[f"Nutzeinheiten_{selected_year}"],
        )

    if year not in YEAR_ORDER:
        raise ValueError(f"Invalid year '{year}'. Must be one of {YEAR_ORDER}.")
    previous_year: str | None = (
        YEAR_ORDER[YEAR_ORDER.index(year) - 1]
        if YEAR_ORDER.index(year) - 1 >= 0
        else None
    )

    total_area_and_units = read_file(
        RESULTS_DIR / f"{distribution_name}.csv", encoding="utf-8"
    )
    shares = get_building_shares()

    buildings = {}
    for _, row in total_area_and_units.iterrows():
        building_name = row["Cluster"]
        based_on = f"{building_name} | {topology}"

        # Get previous units to calc difference
        if previous_year is None:
            previous_units = 0
        else:
            _, previous_units = get_area_and_units_for_year(previous_year)

        current_area, current_units = get_area_and_units_for_year(year)
        if current_area == 0:
            continue

        if row["Übercluster"] == "Wohnen":
            # Building subtype covers existing and new residential buildings
            buildings[building_name] = {
                "based_on": based_on,
                "floorArea": current_area,
                "numApart": current_units,
            }
        else:
            # Non-residential buildings must be separated into existing and new units
            new_units: int = math.floor(
                (current_units - previous_units) * shares[year]["new"]
            )
            existing_units: int = current_units - new_units
            buildings[f"{building_name}_existing"] = {
                "based_on": based_on,
                "floorArea": current_area,
                "numApart": existing_units,
                "buildingSubtype": "existing",
            }
            if new_units == 0:
                continue
            buildings[f"{building_name}_new"] = {
                "based_on": based_on,
                "floorArea": str(current_area),
                "numApart": str(new_units),
                "buildingSubtype": "newBuild",
            }

    return buildings


def create_npro_scenario(
    name: str, weather: str, building_distribution_name: str, year: str, topology: str
) -> None:
    """Create NPRO scenario based on building distribution and weather and store it as YAML in NPRO scenario directory."""
    buildings = get_npro_buildings(building_distribution_name, year, topology)
    scenario_data = {"weather": weather, "buildings": buildings}
    filepath = SCENARIOS_DIR / f"{name}.yaml"
    write_file(
        scenario_data,
        filepath,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def create_all_resq_scenarios() -> None:
    """Create all resq scenarios."""
    period_mapping = {"p1": "statusquo", "p2": "2035", "p3": "2050"}
    for weather_file in WEATHER_DIR.glob("*.txt"):
        period = weather_file.stem.split(".")[1]
        year = period_mapping[period]
        climate = weather_file.stem.split(".")[0][4:]

        for topology in ("central", "decentral", "low_temp_central"):
            scenario_name = f"{year}_{climate}_{topology}"
            npro_topology = "lt-central" if topology == "low_temp_central" else topology
            create_npro_scenario(
                name=scenario_name,
                weather=weather_file.name,
                building_distribution_name=f"total_area_and_units_{topology}_with_forecast",
                year=year,
                topology=npro_topology,
            )


if __name__ == "__main__":
    create_all_resq_scenarios()

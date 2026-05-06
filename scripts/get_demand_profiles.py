"""Module to aggregate demands per scenario extracted from NPRO buildings."""

import json
import pandas as pd
import pathlib
from utils.files import write_file
from settings import RESULTS_DIR

BUILDINGS_DIR = RESULTS_DIR / "npro_buildings"
PROFILES_DIR = RESULTS_DIR / "demand_profiles"


def get_scenario_info(folder_name):
    """Extract year, climate scenario and topology from folder name."""
    parts = folder_name.split("_")
    year = parts[0]
    topology = "_".join(parts[3:])
    climate = "_".join(parts[1:3])
    return year, climate, topology


def aggregate_demands():
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    yearly_demands = {}
    all_profiles = {}  # (year, climate) -> DataFrame

    for scenario_folder in BUILDINGS_DIR.iterdir():
        scenario_path: pathlib.Path = BUILDINGS_DIR / scenario_folder
        if not scenario_path.is_dir():
            continue

        print(f"Processing scenario: {scenario_folder}")
        year, climate, topology = get_scenario_info(scenario_folder.name)
        year_climate = f"{year}_{climate}"

        if (year, climate) not in all_profiles:
            all_profiles[(year, climate)] = pd.DataFrame(
                index=range(8760)
            )  # assuming 8760 hours

        for file in scenario_path.iterdir():
            if file.suffix == ".json":
                json_path = scenario_path / file
                csv_path = scenario_path / file.name.replace(".json", ".csv")

                if not csv_path.exists():
                    print(f"Warning: CSV not found for {json_path}")
                    continue

                with open(json_path, "r") as f:
                    building_info = json.load(f)

                is_residential = building_info.get("buildingType") == "residential"
                res_type = "residential" if is_residential else "non_residential"

                df = pd.read_csv(csv_path)

                # Demand profiles
                # electricity: plugLoadsProfile
                # mobility: emobProfile
                # heat: spaceHeatProfile + dhwProfile
                # cool: spaceCoolProfile + processCoolProfile

                electricity_profile = df["plugLoadsProfile"]
                mobility_profile = df["emobProfile"]
                heat_profile = df["spaceHeatProfile"] + df["dhwProfile"]
                cool_profile = df["spaceCoolProfile"] + df["processCoolProfile"]

                # Point 1: Sum for yearly demands
                key = (year_climate, topology, res_type)
                if key not in yearly_demands:
                    yearly_demands[key] = {
                        "electricity": 0.0,
                        "mobility": 0.0,
                        "heat": 0.0,
                        "cool": 0.0,
                    }

                yearly_demands[key]["electricity"] += electricity_profile.sum()
                yearly_demands[key]["mobility"] += mobility_profile.sum()
                yearly_demands[key]["heat"] += heat_profile.sum()
                yearly_demands[key]["cool"] += cool_profile.sum()

                for demand_name, profile in [
                    ("electricity", electricity_profile),
                    ("mobility", mobility_profile),
                    ("heat", heat_profile),
                    ("cool", cool_profile),
                ]:
                    if demand_name == "heat":
                        col_name = f"{demand_name}_{topology}-{res_type}"
                    else:
                        col_name = f"{demand_name}-{res_type}"
                    if col_name not in all_profiles[(year, climate)].columns:
                        all_profiles[(year, climate)][col_name] = 0.0

                    # Ensure same length
                    if len(profile) == 8760:
                        all_profiles[(year, climate)][col_name] += profile.values
                    else:
                        raise ValueError(
                            f"Unexpected number of columns in profile '{col_name}' for '{year}_{climate}'."
                        )

    data_for_df1 = []
    for (year_climate, topology, res_type), values in yearly_demands.items():
        row = {"year_climate": year_climate}
        for demand_name, val in values.items():
            if demand_name == "heat":
                key = f"{demand_name}_{topology}-{res_type}"
            else:
                key = f"{demand_name}-{res_type}"
            if key not in row:
                row[key] = val
            else:
                row[key] += val
        data_for_df1.append(row)

    df_total = pd.DataFrame(data_for_df1)
    df_total = df_total.groupby(["year_climate"]).first().reset_index()
    df_total.fillna(0, inplace=True)

    # Adapt data to be used by oemof-pipe element-wise data application
    df_demand_transformed = df_total.melt(
        id_vars="year_climate", var_name="name", value_name="amount"
    )
    df_demand_transformed["name"] = df_demand_transformed["name"] + "-demand"
    write_file(df_demand_transformed, RESULTS_DIR / "total_demands.csv", index=False)

    # Save point 2: demand_profiles
    for (year, climate), df_prof in all_profiles.items():
        filename = f"{year}_{climate}.csv"
        year_str = 2025 if year == "statusquo" else year
        timeindex = pd.date_range(f"{year_str}-01-01", periods=8760, freq="h")
        df_normalized = (
            df_prof / df_total[df_total["year_climate"] == f"{year}_{climate}"].iloc[0]
        )
        df_normalized["timeindex"] = timeindex
        write_file(df_normalized, PROFILES_DIR / filename, index=False)


if __name__ == "__main__":
    aggregate_demands()

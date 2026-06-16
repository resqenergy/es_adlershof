"""Calculate air-source heat pump capacities and weighted-mean costs per scenario from NPRO building demands."""

import pandas as pd
import os
import glob
from settings import DATASETS_DIR, ROOT_DIR
from utils.files import write_file
from utils.metadata import write_metadata

from utils.technikkatalog import get_technology_data, Technology, PARAMETER_MAPPING

NPRO_BUILDINGS_DIR = DATASETS_DIR / "npro_buildings"
COP_FILE = ROOT_DIR / "preprocessed" / "ts_hp_air_cop.csv"

HEATPUMP_DIR = DATASETS_DIR / "heatpump_air"
HEATPUMP_DIR.mkdir(parents=True, exist_ok=True)

TECHNIKKATALOG_HP_CAPACITIES = (5, 10, 20, 30, 40, 50, 60, 80, 100)
TECHNIKKATALOG_TECHNOLOGY_NAME = "LuftWP_dezentral"


def calculate_heatpump_capacities_per_building_type(scenario_name, year):
    """
    Calculates heat pump capacity for a given scenario and year.

    Args:
        scenario_name (str): Name of the scenario (e.g., '2035_mean_rcp85')
        year (str): The year to consider ('statusquo', '2035', or '2050')

    Returns:
        pd.DataFrame: Calculated capacities per building type and topology.
    """
    TOPOLOGIES = ["central", "decentral", "low_temp_central"]

    # Load COP
    # The file has a semicolon separator and 'heatpump_air-profile' column
    df_cop = pd.read_csv(COP_FILE, sep=";")
    cop_values = df_cop["heatpump_air-profile"]

    unit_col = f"Nutzeinheiten_{year}"

    all_results = []

    for topology in TOPOLOGIES:
        scenario_folder = f"{scenario_name}_{topology}"
        folder_path = NPRO_BUILDINGS_DIR / scenario_folder

        if not folder_path.exists():
            print(
                f"Warning: Folder {folder_path} does not exist. Skipping topology {topology}."
            )
            continue

        # Load Nutzeinheiten
        units_file = DATASETS_DIR / f"total_area_and_units_{topology}_with_forecast.csv"
        if not units_file.exists():
            print(
                f"Warning: Units file {units_file} does not exist. Skipping topology {topology}."
            )
            continue

        df_units = pd.read_csv(units_file)
        # Cluster is the key. Columns: Cluster, Nutzeinheiten_statusquo, Nutzeinheiten_2035, Nutzeinheiten_2050
        cluster_units = df_units.set_index("Cluster")[unit_col].to_dict()

        # Get all building CSVs in the scenario folder
        building_files = glob.glob(os.path.join(folder_path, "*.csv"))

        # Group heat demand by cluster
        cluster_demands = {}

        for b_file in building_files:
            b_name = os.path.basename(b_file).replace(".csv", "")
            # Determine cluster name. Suffixes like _existing, _new might be present.
            # We need to match it back to cluster_units keys.
            cluster_name = None
            for cluster in cluster_units.keys():
                if b_name.startswith(cluster):
                    cluster_name = cluster
                    break

            if cluster_name is None:
                # Try more flexible matching if needed
                continue

            df_b = pd.read_csv(b_file)
            demand = df_b["spaceHeatProfile"]
            if cluster_name not in cluster_demands:
                cluster_demands[cluster_name] = demand
            else:
                cluster_demands[cluster_name] += demand

        # Calculate for each cluster
        for cluster, total_demand in cluster_demands.items():
            units = cluster_units.get(cluster, 0)
            if units <= 0:
                continue

            mean_demand = total_demand / units
            peak_load = (mean_demand / cop_values).max()

            # for each building txpe define Heatpump capacity as 90% of peak load
            hp_capacity = 0.9 * peak_load

            all_results.append(
                {
                    "Topology": topology,
                    "Cluster": cluster,
                    "Nutzeinheiten": units,
                    "Total_Demand": total_demand.sum(),
                    "Mean_Demand": mean_demand.sum(),
                    "Peak_Load": peak_load,
                    "HP_Capacity_90_Peak": hp_capacity,
                }
            )

    return pd.DataFrame(all_results)


def calculate_heatpump_cost(
    capacities_per_building_type: pd.DataFrame, year: str
) -> pd.DataFrame:
    # 1. Map each HP_Capacity_90_Peak to an available capacity given by TECHNIKKATALOG_HP_CAPACITIES
    # We find the closest capacity (or use another logic? Usually closest or next higher.
    # The prompt says "map each HP_Capacity_90_Peak to an available Capacity given by TECHNIKKATALOG_HP_CAPACITIES"
    # I will use the closest one.
    def get_closest_capacity(capacity):
        return min(TECHNIKKATALOG_HP_CAPACITIES, key=lambda x: abs(x - capacity))

    capacities_per_building_type["Available_Capacity"] = capacities_per_building_type[
        "HP_Capacity_90_Peak"
    ].apply(get_closest_capacity)

    # 2. Get related cost from technikkatalog
    # build Technology mapping
    tech_mapping = {}
    for cap in TECHNIKKATALOG_HP_CAPACITIES:
        tech_mapping[Technology(TECHNIKKATALOG_TECHNOLOGY_NAME, cap)] = (
            f"{TECHNIKKATALOG_TECHNOLOGY_NAME}_{cap}"
        )

    # Load technology data from technikkatalog
    df_tech = get_technology_data(tech_mapping)

    # Join with capacities
    # Available_Capacity is used to match back to tech data.
    # df_tech has 'name' which is like "LuftWP_dezentral_5"
    results = []
    for _, row in capacities_per_building_type.iterrows():
        cap = row["Available_Capacity"]
        tech_id = f"{TECHNIKKATALOG_TECHNOLOGY_NAME}_{cap}"
        tech_costs = df_tech[(df_tech["name"] == tech_id) & (df_tech["Jahr"] == year)]

        if tech_costs.empty:
            continue

        # Extract costs (e.g., capacity_cost_overnight, fixom_cost, etc.)
        # We need to map them back to columns.
        cost_dict = {
            "Topology": row["Topology"],
            "Cluster": row["Cluster"],
            "Nutzeinheiten": row["Nutzeinheiten"],
            "Available_Capacity": cap,
        }
        for _, cost_row in tech_costs.iterrows():
            # var_name is already mapped to English names in get_technology_data
            cost_dict[cost_row["var_name"]] = cost_row["var_value"]

        results.append(cost_dict)

    df_results = pd.DataFrame(results)
    return df_results


def calculate_weighted_mean_cost(df_results: pd.DataFrame) -> dict:
    cost_columns = list(PARAMETER_MAPPING.values())
    # Only keep columns that are actually in df_results
    cost_columns = [col for col in cost_columns if col in df_results.columns]

    summary = {"name": "heatpump_air"}
    total_units = df_results["Nutzeinheiten"].sum()
    if total_units > 0:
        for col in cost_columns:
            weighted_sum = (df_results[col] * df_results["Nutzeinheiten"]).sum()
            summary[col] = weighted_sum / total_units

    return summary


if __name__ == "__main__":
    weighted_cost_list = []
    scenarios = {
        "_".join(scenario_folder.name.split("_")[:3])
        for scenario_folder in NPRO_BUILDINGS_DIR.iterdir()
    }
    for scenario in scenarios:
        year = scenario.split("_")[0]
        year_number = "2025" if year == "statusquo" else year

        _capacities_per_building_type = calculate_heatpump_capacities_per_building_type(
            scenario, year
        )
        heatpump_cost = calculate_heatpump_cost(
            _capacities_per_building_type, year_number
        )
        heatpump_cost.to_csv(HEATPUMP_DIR / f"heatpump_air_{scenario}.csv", index=False)
        weighted_cost = calculate_weighted_mean_cost(heatpump_cost)
        weighted_cost["name"] = "heatpump_air"
        weighted_cost["scenario"] = scenario
        weighted_cost_list.append(weighted_cost)

    weighted_cost_df = pd.DataFrame(weighted_cost_list)
    write_file(weighted_cost_df, HEATPUMP_DIR / "hp_cost.csv", index=False)

    per_scenario_outputs = [
        HEATPUMP_DIR / f"heatpump_air_{scenario}.csv" for scenario in scenarios
    ]
    write_metadata(
        HEATPUMP_DIR,
        script=__file__,
        description="Air-source heat pump capacity and weighted-mean cost per scenario, derived from NPRO building heat demands, COP profiles, and Technikkatalog cost data.",
        inputs=[
            COP_FILE,
            NPRO_BUILDINGS_DIR,
            DATASETS_DIR / "areas_forecast",
        ],
        outputs=[*per_scenario_outputs, HEATPUMP_DIR / "hp_cost.csv"],
        params={
            "technikkatalog_technology": TECHNIKKATALOG_TECHNOLOGY_NAME,
            "available_capacities_kW": list(TECHNIKKATALOG_HP_CAPACITIES),
        },
        sources=[],
    )

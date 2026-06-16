"""Module to calculate capacity costs from overnight capacity costs."""

from pathlib import Path
import pandas as pd

from utils.economics import annuity
from settings import DATASETS_DIR, RAW_DIR
from utils.metadata import write_metadata

TECHNOLOGY_OUTPUT_DIR = DATASETS_DIR / "technology_capacity_cost"
TECHNOLOGY_OUTPUT_DIR.mkdir(exist_ok=True)

SOLAR_OUTPUT_DIR = DATASETS_DIR / "solar_thermal"
SOLAR_OUTPUT_DIR.mkdir(exist_ok=True)

WACC = 0.04


def calculate_annual_cost(
    input_file: Path, output_file: Path, scenario_key: str = "scenario_key"
) -> None:
    """Calculate capacity costs from overnight capacity costs."""
    # Read the costs and efficiencies
    df = pd.read_csv(input_file, sep=";")

    # Results list
    capacity_costs = []

    # Group by scenario and name (technology)
    # Exclude rows where scenario_key is ALL for the calculations
    calc_df = df[df[scenario_key] != "ALL"]
    grouped = calc_df.groupby([scenario_key, "name"])

    for (scenario, name), group in grouped:
        # Get values
        var_values = group.set_index("var_name")["var_value"]

        # Lifetime: lifetime
        lifetime = None
        if "lifetime" in var_values:
            val = var_values["lifetime"]
            if pd.notna(val) and val != "":
                lifetime = int(val)
        if lifetime is None:
            continue

        result = {
            scenario_key: scenario,
            "name": name,
        }
        for suffix in ("", "storage_"):
            if f"{suffix}capacity_cost_overnight" not in var_values:
                continue
            val = var_values[f"{suffix}capacity_cost_overnight"]
            if pd.isna(val) or val == "":
                continue

            capex = float(val)
            ann_capex = annuity(capex, lifetime, WACC)

            # Add fix operational costs
            if f"{suffix}fixom_cost" not in var_values:
                continue
            val = var_values[f"{suffix}fixom_cost"]
            if pd.isna(val) or val == "":
                continue
            fixom = float(val)

            total_annualized_cost = ann_capex + fixom
            result[f"{suffix}capacity_cost"] = total_annualized_cost

        capacity_costs.append(result)

    # Convert to DataFrame and save
    res_df = pd.DataFrame(capacity_costs)
    res_df.to_csv(output_file, index=False, sep=";")
    print(f"Saved results to {output_file}")


if __name__ == "__main__":
    # calculate_annual_cost(
    #     PREPROCESSED_DIR / "scalars" / "costs_efficiencies.csv",
    #     PREPROCESSED_DIR / "scalars" / "capacity_costs.csv",
    # )
    tech_input = DATASETS_DIR / "technology_cost" / "kww_technikkatalog.csv"
    tech_output = TECHNOLOGY_OUTPUT_DIR / "kww_technikkatalog_capacity_cost.csv"
    solar_input = RAW_DIR / "solar_thermal" / "solar_thermal_parameters.csv"
    solar_output = SOLAR_OUTPUT_DIR / "solar_thermal_capacity_cost.csv"

    calculate_annual_cost(tech_input, tech_output, scenario_key="scenario")
    calculate_annual_cost(solar_input, solar_output)

    write_metadata(
        TECHNOLOGY_OUTPUT_DIR,
        script=__file__,
        description="Annualized capacity costs for district heating technologies, computed from overnight CAPEX, lifetime, WACC, and fixed O&M costs.",
        inputs=[tech_input],
        outputs=[tech_output],
        params={"wacc": WACC},
        sources=[],
    )
    write_metadata(
        SOLAR_OUTPUT_DIR,
        script=__file__,
        description="Annualized capacity costs for solar thermal collectors, computed from overnight CAPEX, lifetime, WACC, and fixed O&M costs.",
        inputs=[solar_input],
        outputs=[solar_output],
        params={"wacc": WACC},
        sources=[],
    )

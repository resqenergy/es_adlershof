"""Module to calculate capacity costs from overnight capacity costs."""

from pathlib import Path
import pandas as pd

from economics import annuity

PREPROCESSED_DIR = Path(__file__).parent.parent / "preprocessed"
OVERNIGHT_COSTS_FILE = PREPROCESSED_DIR / "scalars" / "costs_efficiencies.csv"
RESULT_FILEPATH = PREPROCESSED_DIR / "scalars" / "capacity_costs.csv"

WACC = 0.04


def main():
    """Calculate capacity costs from overnight capacity costs."""
    # Read the costs and efficiencies
    df = pd.read_csv(OVERNIGHT_COSTS_FILE, sep=";")

    # Results list
    capacitiy_costs = []

    # Group by scenario and name (technology)
    # Exclude rows where scenario_key is ALL for the calculations
    calc_df = df[df["scenario_key"] != "ALL"]
    grouped = calc_df.groupby(["scenario_key", "name"])

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
            "scenario_key": scenario,
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
            val = var_values["fixom_cost"]
            if pd.isna(val) or val == "":
                continue
            fixom = float(val)

            total_annualized_cost = ann_capex + fixom
            result[f"{suffix}capacity_cost"] = total_annualized_cost

        capacitiy_costs.append(result)

    # Convert to DataFrame and save
    res_df = pd.DataFrame(capacitiy_costs)
    res_df.to_csv(RESULT_FILEPATH, index=False, sep=";")
    print(f"Saved results to {RESULT_FILEPATH}")


if __name__ == "__main__":
    main()

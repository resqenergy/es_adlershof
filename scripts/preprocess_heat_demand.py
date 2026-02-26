"""Module to preprocess the heat demand data"""
from typing import Any

import pandas as pd
from pathlib import Path

from pandas import DataFrame, Series

RAW_DIR = Path(__file__).parent.parent / "raw"
HEAT_LOAD_DIR = RAW_DIR / "heat_load"
DISTRIBUTION_HOUSEHOLDS_FILE = RAW_DIR / "distribution_households.csv"

PREPROCESSED_DIR = Path(__file__).parent.parent / "preprocessed"
TIMESERIES_OUTPUT = PREPROCESSED_DIR / "ts_heat_load.csv"

HEAT_COLUMN = "Wärme gesamt (kW)"
ELECTRICITY_COLUMN = "Strom gesamt (kW)"

HEAT_MAPPING = {
    "sfh": "heat_decentral",
    "mfh": "heat_central",
    "ghd": "heat_central",
    "lab": "heat_central",
    "uni": "heat_central",
    "office": "heat_central"
}


def preprocess_heat_demand(region: str = "AD", year: int = 2050):
    """Preprocess the heat demand data"""
    distribution_df = pd.read_csv(DISTRIBUTION_HOUSEHOLDS_FILE, index_col="region")

    if region not in distribution_df.index:
        raise ValueError(f"Region {region} not found in distribution file.")

    filtered_distribution = distribution_df.loc[region]
    distribution = filtered_distribution.to_dict()

    all_timeseries = []

    for type_name in distribution:
        filename = f"{type_name}_{region}_{year}.csv"
        res_df = get_heat_timeseries(type_name, distribution, filename)
        all_timeseries.append(res_df)

    # Combine all types
    result_df = pd.concat(all_timeseries, axis=1)

    # Calculate aggregated timeseries (total)
    heat_central_cols = [f"{c}_heat" for c, heat_type in HEAT_MAPPING.items() if heat_type == "heat_central"]
    heat_decentral_cols = [f"{c}_heat" for c, heat_type in HEAT_MAPPING.items() if heat_type == "heat_decentral"]
    elec_cols = [c for c in result_df.columns if "electricity" in c]

    result_df["heat_central-demand-profile"] = result_df[heat_central_cols].sum(axis=1)
    result_df["heat_decentral-demand-profile"] = result_df[heat_decentral_cols].sum(axis=1)
    result_df["electricity-demand-profile"] = result_df[elec_cols].sum(axis=1)

    # Ensure output directory exists
    PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Add timeindex
    result_df["timeindex"] = pd.date_range(start=f"{year}-01-01 00:00:00", freq="h", periods=len(result_df))

    # Store in TIMESERIES_OUTPUT
    result_df.to_csv(TIMESERIES_OUTPUT, index=False, sep=";")
    print(f"Preprocessed heat demand saved to {TIMESERIES_OUTPUT}")


def get_heat_timeseries(type_name: str, distribution: dict, filename: str) -> Series:
    filepath = HEAT_LOAD_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Heat load file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Check for required columns
    if HEAT_COLUMN not in df.columns or ELECTRICITY_COLUMN not in df.columns:
        raise ValueError(f"Required columns missing in {filepath}")

    # Multiply by distribution
    dist_value = distribution[type_name]
    df[f"{type_name}_heat"] = df[HEAT_COLUMN] * dist_value
    df[f"{type_name}_electricity"] = df[ELECTRICITY_COLUMN] * dist_value

    # Keep only relevant columns
    res_df = df[[f"{type_name}_heat", f"{type_name}_electricity"]]
    return res_df


if __name__ == "__main__":
    preprocess_heat_demand()



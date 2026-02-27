"""Module to preprocess the heat demand data"""

from collections import defaultdict

import pandas as pd
from pathlib import Path

from pandas import Series

RAW_DIR = Path(__file__).parent.parent / "raw"
PREPROCESSED_DIR = Path(__file__).parent.parent / "preprocessed"

BUILDING_DISTRIBUTION_FILE = RAW_DIR / "distribution_households.csv"

HEAT_LOAD_DIR = RAW_DIR / "heat_load"
HEAT_OUTPUT_FILE = PREPROCESSED_DIR / "ts_heat_load.csv"
HEAT_COLUMN = "Wärme gesamt (kW)"
HEAT_MAPPING = {
    "sfh": "heat_decentral-demand-profile",
    "mfh": "heat_central-demand-profile",
    "ghd": "heat_central-demand-profile",
    "lab": "heat_central-demand-profile",
    "uni": "heat_central-demand-profile",
    "office": "heat_central-demand-profile",
}

ELECTRICITY_LOAD_DIR = RAW_DIR / "electricity_load"
ELECTRICITY_OUTPUT_FILE = PREPROCESSED_DIR / "ts_electricity_load.csv"
ELECTRICITY_COLUMN = "Zone 1 (kW)"
ELECTRICITY_MAPPING = {
    "sfh": "electricity-demand-profile",
    "mfh": "electricity-demand-profile",
    "ghd": "electricity-demand-profile",
    "lab": "electricity-demand-profile",
    "uni": "electricity-demand-profile",
    "office": "electricity-demand-profile",
}


def get_building_distribution(region: str) -> dict:
    """Return building distribution for given region."""
    distribution_df = pd.read_csv(BUILDING_DISTRIBUTION_FILE, index_col="region")

    if region not in distribution_df.index:
        raise ValueError(f"Region {region} not found in distribution file.")

    filtered_distribution = distribution_df.loc[region]
    distribution = filtered_distribution.to_dict()
    return distribution


def preprocess_demand(
    directory: Path,
    column: str,
    mapping: dict[str, str],
    output_filename: Path,
    scaling_factor: float = 1.0,
    region: str = "AD",
    year: int = 2050,
):
    """Preprocess the heat demand data"""

    building_distribution = get_building_distribution(region)

    all_timeseries = []
    for type_name in building_distribution:
        filename = f"{type_name}_{region}_{year}.csv"
        timeseries = get_timeseries(column, filename, directory)
        timeseries.name = type_name

        # Multiply by distribution
        dist_value = building_distribution[type_name]
        timeseries = timeseries * dist_value * scaling_factor
        all_timeseries.append(timeseries)

    # Combine all types
    result_df = pd.concat(all_timeseries, axis=1)

    # Add timeindex
    result_df["timeindex"] = pd.date_range(
        start=f"{year}-01-01 00:00:00", freq="h", periods=len(result_df)
    )

    total_columns = defaultdict(list)
    for column, target_column in mapping.items():
        total_columns[target_column].append(column)

    for target_column, columns in total_columns.items():
        result_df[target_column] = result_df[columns].sum(axis=1)

    # Ensure output directory exists
    PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Store in TIMESERIES_OUTPUT
    result_df.to_csv(output_filename, index=False, sep=";")
    print(f"Preprocessed heat demand saved to {output_filename}")


def get_timeseries(column: str, filename: str, directory: Path) -> Series:
    filepath = directory / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Timeseries file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Check for required columns
    if column not in df.columns:
        raise ValueError(f"Required columns missing in {filepath}")

    return df[column]


if __name__ == "__main__":
    preprocess_demand(
        HEAT_LOAD_DIR, HEAT_COLUMN, HEAT_MAPPING, HEAT_OUTPUT_FILE, scaling_factor=1e-3
    )
    preprocess_demand(
        ELECTRICITY_LOAD_DIR,
        ELECTRICITY_COLUMN,
        ELECTRICITY_MAPPING,
        ELECTRICITY_OUTPUT_FILE,
        scaling_factor=1e-3,
    )

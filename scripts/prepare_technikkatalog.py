"""
This module prepares flat data from Technikkatalog to be used by oemof-pipe.

Steps:
1. Last sheet (flatdata_all) of Technikkatalog must be extracted and saved as CSV.
2. Adapt name (depending on ES component names and capacity dimensions) and parameters (depending on oemof.solph attributes) to your needs.
3. Run this script.
4. Use resulting CSV in oemof-pipe scenario
"""

import pathlib
import pandas as pd
import numpy as np


NAME_MAPPING = {"AbwaermeWP_zentral_0,3": "heatpump_22", "BHKW_zentral_0,3": "bhkw"}
PARAMETER_MAPPING = {
    "Spezifische Investitionskosten": "capacity_cost_overnight",
    "Wirkungsgrad thermisch": "thermal_efficiency",
    "Wirkungsgrad elektrisch": "electric_efficiency",
    "Lebensdauer": "lifetime",
    "Jährliche Fixkosten O&M": "fixom_cost",
}

PARAMETER_PREPROCESSING = {
    "Wirkungsgrad thermisch": lambda x: x / 100,
    "Wirkungsgrad elektrisch": lambda x: x / 100,
}

ROOT_DIR = pathlib.Path(__file__).parent.parent
RAW_DIR = ROOT_DIR / "raw"
PREPROCESSED_DIR = ROOT_DIR / "preprocessed"

FLATDATA_FILE_RAW = (
    RAW_DIR / "KWW-Technikkatalog-Waermeplanung_12-2025(flatdata_all).csv"
)
FLATDATA_FILE_PREPROCESSED = PREPROCESSED_DIR / "kww_technikkatalog.csv"

FORECAST_YEARS = (2035, 2050)


# Add forecast
def calculate_forecast(costs_per_year: dict[int, float], target_year: int) -> float:
    """
    Calculate forecast value based on linear interpolation/extrapolation.

    Args:
        costs_per_year: Dictionary with years as keys and costs as values
        target_year: Year for which to calculate the forecasted value

    Returns:
        Interpolated or extrapolated cost value for target_year
    """
    years = sorted(costs_per_year.keys())
    costs = [costs_per_year[year] for year in years]

    if not years:
        return 0.0
    if len(years) < 2:
        return costs[0]

    return float(np.interp(target_year, years, costs, left=None, right=None))


def load_and_clean_data(file_path: pathlib.Path) -> pd.DataFrame:
    """Load raw data and perform initial cleaning and type conversion."""
    df = pd.read_csv(file_path, encoding="iso-8859-1", sep=";", dtype={"Jahr": str})
    df = df.rename(columns={"Parameter": "var_name", "Wert": "var_value"})

    # Values are not parsed correctly due to unknown values. Filter non-numeric values
    df["var_value"] = (
        df["var_value"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    # Filter rows where conversion to float fails
    df = df[pd.to_numeric(df["var_value"], errors="coerce").notna()]
    df["var_value"] = df["var_value"].astype(float)
    return df


def preprocess_parameters(
    df: pd.DataFrame, preprocessing_mapping: dict
) -> pd.DataFrame:
    """Apply preprocessing functions to specific parameters."""
    for parameter, parameter_function in preprocessing_mapping.items():
        matching_rows = df.loc[df["var_name"].str.contains(parameter, na=False)]
        df.loc[matching_rows.index, "var_value"] = matching_rows["var_value"].apply(
            parameter_function
        )
    return df


def add_forecasts(df: pd.DataFrame, forecast_years: tuple[int, ...]) -> pd.DataFrame:
    """Calculate and add forecast rows for capacity costs and O&M costs."""
    forecast_rows = []
    for technologie in df["Technologie"].unique():
        name_data = df[df["Technologie"] == technologie]

        # Get forecast parameters
        a = {}
        b = {}
        try:
            for year in (2025, 2030, 2040):
                a[year] = name_data.loc[
                    (name_data["var_name"] == "Parameter a")
                    & (name_data["Jahr"] == str(year)),
                    "var_value",
                ].iloc[0]
                b[year] = name_data.loc[
                    (name_data["var_name"] == "Parameter b")
                    & (name_data["Jahr"] == str(year)),
                    "var_value",
                ].iloc[0]
        except IndexError:
            continue

        capacity_cost_data = name_data[name_data["var_name"] == "Thermische Leistung"]
        for idx, row in capacity_cost_data.iterrows():

            # Get capacity in kWth
            capacity = row["var_value"]
            if row["Dimensionierungseinheit"] == "MWth":
                capacity *= 1000

            # Calculate costs per year using formula
            costs_per_year = {}
            for year in a:
                costs_per_year[year] = a[year] * capacity ** b[year]

            for forecast_year in forecast_years:
                # Calculate capacity cost from forecasted total cost
                forecast_value = (
                    calculate_forecast(costs_per_year, forecast_year) / capacity
                )

                # Create new row with forecast scenario
                forecast_row = row.copy()
                forecast_row["Jahr"] = str(forecast_year)
                forecast_row["var_name"] = "Spezifische Investitionskosten"
                forecast_row["var_value"] = forecast_value
                forecast_rows.append(forecast_row)

        # Copy OM cost for each forecast year
        fixom_cost_data = name_data[name_data["var_name"] == "Jährliche Fixkosten O&M"]
        for idx, row in fixom_cost_data.iterrows():
            for forecast_year in forecast_years:
                # Create new row with copied O&M cost (as they stay the same)
                forecast_row = row.copy()
                forecast_row["Jahr"] = str(forecast_year)
                forecast_rows.append(forecast_row)

    if forecast_rows:
        forecast_df = pd.DataFrame(forecast_rows)
        df = pd.concat([df, forecast_df], ignore_index=True)
    return df


def apply_mappings_and_format(
    df: pd.DataFrame, name_mapping: dict, parameter_mapping: dict
) -> pd.DataFrame:
    """Rename scenarios, merge technology/dimension, and apply final mappings."""
    # Rename scenario entries as oemof-pipe will otherwise read them as int which causes errors
    df["scenario"] = "scenario_" + df["Jahr"]

    # We need to merge technology and dimension as values depend on both
    df["name"] = df.apply(
        lambda row: f'{row["Technologie"]}_{row["Dimensionierung"]}', axis=1
    )

    # Apply mapping if needed
    df["name"] = df["name"].map(name_mapping)
    df = df.dropna(subset=["name"])
    df["var_name"] = df["var_name"].map(parameter_mapping)
    return df


def main():
    # Load raw data
    raw_data = load_and_clean_data(FLATDATA_FILE_RAW)

    # Preprocess parameters if function is given:
    raw_data = preprocess_parameters(raw_data, PARAMETER_PREPROCESSING)

    # Add forecast
    raw_data = add_forecasts(raw_data, FORECAST_YEARS)

    # Apply final mappings and formatting
    raw_data = apply_mappings_and_format(raw_data, NAME_MAPPING, PARAMETER_MAPPING)

    # Save to CSV
    raw_data.to_csv(FLATDATA_FILE_PREPROCESSED, index=False, sep=";")


if __name__ == "__main__":
    main()

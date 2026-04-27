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


# Load raw data
raw_data = pd.read_csv(
    FLATDATA_FILE_RAW, encoding="iso-8859-1", sep=";", dtype={"Jahr": str}
)
raw_data = raw_data.rename(columns={"Parameter": "var_name", "Wert": "var_value"})

# Values are not parsed correctly due to unknown values. Filter non-numeric values
raw_data["var_value"] = (
    raw_data["var_value"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)
# Filter rows where conversion to float fails
raw_data = raw_data[pd.to_numeric(raw_data["var_value"], errors="coerce").notna()]
raw_data["var_value"] = raw_data["var_value"].astype(float)

# Preprocess parameters if function is given:
for parameter, parameter_function in PARAMETER_PREPROCESSING.items():
    matching_rows = raw_data.loc[raw_data["var_name"].str.contains(parameter, na=False)]
    raw_data.loc[matching_rows.index, "var_value"] = matching_rows["var_value"].apply(
        parameter_function
    )

forecast_rows = []
for technologie in raw_data["Technologie"].unique():
    name_data = raw_data[raw_data["Technologie"] == technologie]

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

        for forecast_year in FORECAST_YEARS:
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
        for forecast_year in FORECAST_YEARS:
            # Create new row with copied O&M cost (as they stay the same)
            forecast_row = row.copy()
            forecast_row["Jahr"] = str(forecast_year)
            forecast_rows.append(forecast_row)

if forecast_rows:
    forecast_df = pd.DataFrame(forecast_rows)
    raw_data = pd.concat([raw_data, forecast_df], ignore_index=True)

# Rename scenario entries as oemof-pipe will otherwise read them as int which causes errors
raw_data["scenario"] = "scenario_" + raw_data["Jahr"]

# We need to merge technology and dimension as values depend on both
raw_data["name"] = raw_data.apply(
    lambda row: f'{row["Technologie"]}_{row["Dimensionierung"]}', axis=1
)

# Apply mapping if needed
raw_data["name"] = raw_data["name"].map(NAME_MAPPING)
raw_data = raw_data.dropna(subset=["name"])
raw_data["var_name"] = raw_data["var_name"].map(PARAMETER_MAPPING)


# Save to CSV
raw_data.to_csv(FLATDATA_FILE_PREPROCESSED, index=False, sep=";")

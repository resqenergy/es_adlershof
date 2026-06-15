"""
This module prepares flat data from Technikkatalog to be used by oemof-pipe.

Steps:
1. Last sheet (flatdata_all) of Technikkatalog must be extracted and saved as CSV.
2. Adapt name (depending on ES component names and capacity dimensions) and parameters (depending on oemof.solph attributes) to your needs.
3. Run this script.
4. Use resulting CSV in oemof-pipe scenario
"""

from collections import namedtuple
import pathlib
import pandas as pd
import numpy as np

from settings import RAW_DIR

TECHNOLOGY_DIR = RAW_DIR / "technikkatalog"
FLATDATA_FILE_RAW = (
    TECHNOLOGY_DIR / "KWW-Technikkatalog-Waermeplanung_12-2025(flatdata_all).csv"
)

Technology = namedtuple("Technology", ["name", "capacity"])

PARAMETER_MAPPING = {
    "Spezifische Investitionskosten": "capacity_cost_overnight",
    "Wirkungsgrad thermisch": "thermal_efficiency",
    "Wirkungsgrad elektrisch": "electric_efficiency",
    "Lebensdauer": "lifetime",
    "Jährliche Fixkosten O&M": "fixom_cost",
    "Variable Kosten O&M": "marginal_cost",
}

PARAMETER_PREPROCESSING = {
    "Wirkungsgrad thermisch": lambda value, _capacity: value / 100,
    "Wirkungsgrad elektrisch": lambda value, _capacity: value / 100,
    "Jährliche Fixkosten O&M": lambda value, capacity: value / capacity,
}

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


def _get_capacity_kwth(df: pd.DataFrame, row: pd.Series) -> float:
    """Look up thermal capacity in kWth for a given row's technology and dimensionierung."""
    cap_rows = df[
        (df["Technologie"] == row["Technologie"])
        & (df["Dimensionierung"] == row["Dimensionierung"])
        & (df["Jahr"] == row["Jahr"])
        & (df["var_name"] == "Thermische Leistung")
    ]
    if cap_rows.empty:
        return 1.0
    capacity = cap_rows["var_value"].iloc[0]
    if cap_rows["Dimensionierungseinheit"].iloc[0] == "MWth":
        capacity *= 1000
    return float(capacity)


def preprocess_parameters(
    df: pd.DataFrame,
    preprocessing_mapping: dict,
    technology_mapping: dict[Technology, str],
) -> pd.DataFrame:
    """Apply preprocessing functions to specific parameters.

    Args:
        df: Raw technology data.
        preprocessing_mapping: Maps parameter name substrings to functions ``(value, capacity_kwth) -> float``.
        technology_mapping: Technology mapping used to resolve the capacity column per technology.
    """
    for parameter, parameter_function in preprocessing_mapping.items():
        matching_indices = df.index[df["var_name"].str.contains(parameter, na=False)]
        for idx in matching_indices:
            row = df.loc[idx]
            capacity = _get_capacity_kwth(df, row)
            df.at[idx, "var_value"] = parameter_function(row["var_value"], capacity)
    return df


def add_zusaetzliche_kosten(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'Zusätzliche Kosten' on top of 'Spezifische Investitionskosten'.

    The raw CSV stores them separately. Forecast years already include both
    because the formula is fitted to 'Investitionskosten gesamt'.
    """
    zusatz = df[df["var_name"].str.strip() == "Zusätzliche Kosten"].copy()
    if zusatz.empty:
        return df

    for idx, row in df[df["var_name"] == "Spezifische Investitionskosten"].iterrows():
        match = zusatz[
            (zusatz["Technologie"] == row["Technologie"])
            & (zusatz["Dimensionierung"] == row["Dimensionierung"])
            & (zusatz["Jahr"] == row["Jahr"])
        ]
        if not match.empty:
            df.at[idx, "var_value"] += match["var_value"].iloc[0]
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

        # Copy parameters for each forecast year
        for parameter in PARAMETER_MAPPING:
            if parameter == "Spezifische Investitionskosten":
                continue
            parameter_data = name_data[name_data["var_name"] == parameter]
            for idx, row in parameter_data.iterrows():
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
    df: pd.DataFrame, technology_mapping: dict[Technology, str], parameter_mapping: dict
) -> pd.DataFrame:
    """Rename scenarios, merge technology/dimension, and apply final mappings."""
    # Rename scenario entries as oemof-pipe will otherwise read them as int which causes errors
    df["scenario"] = "scenario_" + df["Jahr"]

    # We need to merge technology and dimension as values depend on both
    df["name"] = df.apply(
        lambda row: f'{row["Technologie"]}_{row["Dimensionierung"]}', axis=1
    )

    # Apply mapping if needed
    technology_mapping = {
        f'{technology.name}_{str(technology.capacity).replace(".", ",")}': new_name
        for technology, new_name in technology_mapping.items()
    }
    df["name"] = df["name"].map(technology_mapping)
    df["var_name"] = df["var_name"].map(parameter_mapping)
    df = df.dropna(subset=["name", "var_name"])
    df.sort_values(["name", "var_name", "Jahr"], inplace=True)
    return df


def get_technology_data(technology_mapping: dict):
    # Load raw data
    raw_data = load_and_clean_data(FLATDATA_FILE_RAW)

    # Preprocess parameters if function is given:
    preprocessed_data = preprocess_parameters(
        raw_data, PARAMETER_PREPROCESSING, technology_mapping
    )

    # Add Zusätzliche Kosten to Spezifische Investitionskosten
    preprocessed_data = add_zusaetzliche_kosten(preprocessed_data)

    # Add forecast
    forecast_data = add_forecasts(preprocessed_data, FORECAST_YEARS)

    # Apply final mappings and formatting
    parameter_data = apply_mappings_and_format(
        forecast_data, technology_mapping, PARAMETER_MAPPING
    )
    return parameter_data

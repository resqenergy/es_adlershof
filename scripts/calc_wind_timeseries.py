import warnings
from pathlib import Path

import pandas as pd
from windpowerlib import ModelChain, WindTurbine

from utils.files import write_file, read_file

ROOT_DIR = Path(__file__).parent.parent
RAW_DIR = ROOT_DIR / "raw"
RESULTS_DIR = ROOT_DIR / "results" / "wind_timeseries"
WEATHER_DATA_DIR = ROOT_DIR / "npro_weather"
TURBINE_MODELS_NREL = RAW_DIR / "wind_turbine_models"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

args = {
    "year": None,
    "periods": 8760,
    "coords": (52.43, 13.54),  # coords of pv plant (52.43, 13.54) => Adlershof (Berlin)
    "roughness_length": 0.6,  # Source: https://wind-data.ch/tools/profile.php?h=2&v=10&z0=0.6&abfrage=Aktualisieren
    "weather_columns": [
        ("pressure", 0),
        ("temperature", 2),
        ("wind_speed", 10),
        ("roughness_length", 0),
    ],  # (variable name, heights) source: heights taken from data/10_Testreferenzjahre_TRY/metadata_testreferenceyears.pdf
    "wind_turbine_name": "2019COE_DW100_100kW_27.6",  # assumption: Wind turbine class "Commercial", source: https://www.osti.gov/servlets/purl/2479271?utm_source=consensus and https://github.com/NREL/turbine-models
    "wind_turbine_class": "Distributed",
    "wind_turbine_hub_height": 40,
    "wind_turbine_nominal_power": 100000,
}

modelchain_data = {
    "wind_speed_model": "logarithmic",  # 'logarithmic' (default),
    # 'hellman' or
    # 'interpolation_extrapolation'
    "density_model": "ideal_gas",  # 'barometric' (default), 'ideal_gas'
    #  or 'interpolation_extrapolation'
    "temperature_model": "linear_gradient",  # 'linear_gradient' (def.) or
    # 'interpolation_extrapolation'
    "power_output_model": "power_coefficient_curve",  # 'power_curve' (default) or
    # 'power_coefficient_curve'
    "density_correction": True,  # False (default) or True
    "obstacle_height": 0,  # default: 0
    "hellman_exp": None,
}  # None (default) or None


def resolve_year(weatherdata_name, year=None):
    """Resolve the calendar year for a TRY weather data file.

    The year can be derived from a period key in the filename ('p1', 'p2', 'p3',
    'reference') or supplied explicitly via args['year']. Providing both is an error.

    Period-to-year mapping:
        p1        -> 2020  (near-future climate scenario)
        p2        -> 2035  (mid-future climate scenario)
        p3        -> 2050  (far-future climate scenario)
        reference -> 2011  (historical reference year)

    Args:
        weatherdata_name (str): Filename (or path string) of the TRY weather file.
        year (int | None): Explicit year override from args['year']. Must be in
            [2000, 2500] if provided. Defaults to args['year'] (None).

    Returns:
        int: The resolved calendar year.

    Raises:
        ValueError: If both a period key and an explicit year are given, if neither
            is given, or if the explicit year is outside [2000, 2500].
    """
    period_map = {
        "p1": 2020,
        "p2": 2035,
        "p3": 2050,
        "reference": 2011,
    }  # eigene Annahme hstorisches Referenzjahr

    # Check if any period key is present in the name
    period_in_name = next((k for k in period_map if k in weatherdata_name), None)

    if year is not None and period_in_name is not None:
        raise ValueError(
            "Ambiguous input: Provide either args['year'] OR valid weatherdata file and name including "
            "('p1', 'p2', 'p3') in WEATHERDATA_NAME - not both."
        )

    if year is None:
        if period_in_name is not None:
            return period_map[period_in_name]
        raise ValueError(
            "Missing year: WEATHERDATA_NAME must include 'p1', 'p2', or 'p3', "
            "or provide args['year'] manually."
        )

    if 2000 <= year <= 2500:
        warnings.warn(
            "Manual year provided. Ensure consistency with args['periods'].",
            UserWarning,
        )
        return year

    raise ValueError("args['year'] must be between 2000 and 2500.")


def read_and_preprocess_weather_data(weatherdata_file):
    """Read and preprocess a TRY weather file into the windpowerlib MultiIndex format.

    Reads the semicolon-separated TRY file, selects the relevant columns, converts
    temperature from °C to Kelvin, adds a constant roughness-length column, and
    returns a DataFrame with a two-level column MultiIndex as expected by windpowerlib
    (see data/windpowerlib_weather.csv for the reference structure).

    The calendar year is resolved automatically from the filename via resolve_year().
    Column names and measurement heights for the MultiIndex are taken from
    args['weather_columns'].

    Args:
        weatherdata_file (str | Path): Path to the TRY weather file (.txt, semicolon-separated).

    Returns:
        pd.DataFrame: Hourly time series indexed by a DatetimeIndex, with a
            MultiIndex column (variable_name, height). Contains pressure [Pa],
            temperature [K], wind speed [m/s], and roughness length [m].
    """
    year = resolve_year(weatherdata_file.name, args["year"])
    columns = ["pressure_surface", "wind_speed", "air_temperature_mean"]

    df = read_file(weatherdata_file, sep=";", usecols=columns)
    df = df.set_index(
        pd.date_range(start=f"1/1/{year}", periods=args["periods"], freq="h")
    )

    df = df.rename(
        columns={"pressure_surface": "pressure", "air_temperature_mean": "temperature"}
    )
    df["roughness_length"] = args["roughness_length"]

    # transfer temperature from °C to Kelvin
    df["temperature"] = df["temperature"] + 273.15

    df = df[["pressure", "temperature", "wind_speed", "roughness_length"]]
    df.columns = pd.MultiIndex.from_tuples(
        args["weather_columns"], names=["variable_name", "height"]
    )

    return df


def preprocess_nrel_turbine_model(nrel_turbine_model_path):
    columns = ["Wind Speed [m/s]", "Power [kW]"]
    power_curve_df = read_file(nrel_turbine_model_path, usecols=columns)
    power_curve_df = power_curve_df.rename(
        columns={
            "Wind Speed [m/s]": "wind_speed",
            "Power [kW]": "value",
            "Cp [-]": "cp",
        }
    )

    # convert power from kW to W
    power_curve_df["value"] = power_curve_df["value"] * 1000

    turbine_model = {
        "nominal_power": args["wind_turbine_nominal_power"],  # in W
        "hub_height": args["wind_turbine_hub_height"],  # in m
        "power_curve": power_curve_df,
    }
    return turbine_model


def normalize_wind_timeseries(wind_timeseries, nominal_value):
    """Normalize a wind power time series by its nominal power.

    Args:
        wind_timeseries (pd.Series): Wind power output time series [W].
        nominal_value (float): Nominal power of the wind turbine [W].

    Returns:
        pd.Series: Normalized power output, rounded to 7 decimal places.
    """
    wind_timeseries_normalized = round(wind_timeseries / nominal_value, 7)
    return wind_timeseries_normalized


def rename_wind_timeseries(wind_timeseries, column_name, index_name):
    """Set the name and index name of a wind power time series.

    Args:
        wind_timeseries (pd.Series): Wind power time series to rename.
        column_name (str): Name to assign to the Series (becomes column name on export).
        index_name (str): Name to assign to the index.

    Returns:
        pd.Series: The same Series with updated name and index name.
    """
    wind_timeseries.name = column_name
    wind_timeseries.index.name = index_name
    return wind_timeseries


def run_windpowerlib(turbine_model, modelchain_data, weather_windpowerlib):
    """Run the windpowerlib ModelChain and return the turbine with power output.

    Args:
        turbine_model (dict): Turbine specification with keys 'nominal_power' [W],
            'hub_height' [m], and 'power_curve' (pd.DataFrame with 'wind_speed'
            and 'value' columns).
        modelchain_data (dict): ModelChain configuration (wind speed model,
            density model, temperature model, etc.).
        weather_windpowerlib (pd.DataFrame): Hourly weather data with MultiIndex
            columns (variable_name, height) as returned by
            read_and_preprocess_weather_data().

    Returns:
        WindTurbine: windpowerlib WindTurbine object with power_output attribute
            set to the simulated hourly power output time series [W].
    """
    # power curve values and nominal power must be in Watt

    # initialize WindTurbine object
    my_turbine = WindTurbine(**turbine_model)

    # own specifications for ModelChain setup

    mc_my_turbine = ModelChain(my_turbine).run_model(weather_windpowerlib)
    # write power output time series to WindTurbine object
    my_turbine.power_output = mc_my_turbine.power_output

    return my_turbine


if __name__ == "__main__":
    for file in WEATHER_DATA_DIR.iterdir():
        if file.is_file() and file.suffix == ".txt" in file.name:

            weather_windpowerlib = read_and_preprocess_weather_data(file)

            turbine_model_path = (
                TURBINE_MODELS_NREL
                / args["wind_turbine_class"]
                / f"{args['wind_turbine_name']}.csv"
            )
            turbine_model = preprocess_nrel_turbine_model(turbine_model_path)

            my_turbine = run_windpowerlib(
                turbine_model, modelchain_data, weather_windpowerlib
            )

            wind_timeseries = my_turbine.power_output
            wind_timeseries_normalized = normalize_wind_timeseries(
                wind_timeseries, args["wind_turbine_nominal_power"]
            )

            wind_timeseries_normalized = rename_wind_timeseries(
                wind_timeseries_normalized, "wind_profile", "timeindex"
            )

            result_path = (
                RESULTS_DIR
                / f"wind_timeseries-{file.stem}-{wind_timeseries_normalized.index.year[0]}.csv"
            )
            write_file(wind_timeseries_normalized, result_path)

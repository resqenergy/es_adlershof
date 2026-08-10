"""Generate normalized wind power time series from TRY weather data using windpowerlib."""

import re
import warnings

import pandas as pd
import numpy as np
from windpowerlib import ModelChain, WindTurbine

from settings import RAW_DIR, DATASETS_DIR
from utils.metadata import write_metadata

WEATHER_DATA_DIR = RAW_DIR / "weather"
TURBINE_MODELS_NREL = RAW_DIR / "wind_turbine_models"
RESULTS_DIR = DATASETS_DIR / "wind_profiles"
RESULTS_DIR.mkdir(exist_ok=True)

RUN_CONFIG_DATA={
    "year": None,
    "periods": 8760,
}

SITE_CONFIG_DATA= {
    "coords": (52.43, 13.54),  # coords of pv plant (52.43, 13.54) => Adlershof (Berlin)
    "roughness_length": 0.091,  # Source: TUB.Klima Messwerte (Median)
    "roughness_length_freifeld": 0.03,  # Source: WMO Guide to Meteorological Instruments and Methods
    # of Observation; ECMWF Forecast User Guide, Section 9.3.
    "displacement_height": 16.57,  # Source: Messewerte TUB.Klima (Median)
    "blending_height": 60 # Blending height for the two-stage log-profile extrapolation (see
    # extrapolate_to_blending_height() below). Literature value ~60 m, 40-80 m
    # range acceptable. Source: Zhao et al. (2022), Meteorological Applications,
    # DOI: 10.1002/met.2094; Wieringa (1976), QJRMS.
}


WIND_TURBINE_DATA= {
    "wind_turbine_name": "2019COE_DW100_100kW_27.6",
    # assumption: Wind turbine class "Commercial", source: https://www.osti.gov/servlets/purl/2479271?utm_source=consensus and https://github.com/NREL/turbine-models
    "wind_turbine_class": "Distributed",
    "wind_turbine_hub_height": 40,
    "wind_turbine_nominal_power": 100000,
}

MODELCHAIN_DATA = {
    "wind_speed_model": "logarithmic",  # 'logarithmic' (default),
    # 'hellman' or
    # 'interpolation_extrapolation'
    "density_model": "barometric",  # 'barometric' (default), 'ideal_gas'
    #  or 'interpolation_extrapolation'
    "temperature_model": "linear_gradient",  # 'linear_gradient' (def.) or
    # 'interpolation_extrapolation'
    "power_output_model": "power_curve",  # 'power_curve' (default) or
    # 'power_coefficient_curve'
    "density_correction": False,  # False (default) or True
    "obstacle_height": SITE_CONFIG_DATA["displacement_height"] / 0.7, # windpowerlib
    # estimates d = 0.7 * obstacle_height internally, so back solve for the
     # obstacle_height that reproduces our measured displacement_height.
     # Applied from SITE_CONFIG_DATA["blending_height"] to hub_height (second extrapolation
     # stage) - see read_and_preprocess_weather_data() for the first stage.
    "hellman_exp": None,  # None (default) or None
}

WEATHER_COLUMNS= [ #(column_names, heights of measurement in m
    ("pressure", 0),
    ("temperature", 2),
    ("wind_speed", SITE_CONFIG_DATA["blending_height"]),
    ("roughness_length", 0)]


def resolve_year(weatherdata_name, year=None):
    """Resolve the calendar year for a TRY weather data file.

    The year can be derived from a period key in the filename ('p1', 'p2', 'p3',
    'reference') or supplied explicitly via SITE_CONFIG_DATA['year']. Providing both is an error.

    Period-to-year mapping:
        p1        -> 2020  (near-future climate scenario)
        p2        -> 2035  (mid-future climate scenario)
        p3        -> 2050  (far-future climate scenario)
        reference -> 2011  (historical reference year)

    Args:
        weatherdata_name (str): Filename (or path string) of the TRY weather file.
        year (int | None): Explicit year override from SITE_CONFIG_DATA['year']. Must be in
            [2000, 2500] if provided. Defaults to SITE_CONFIG_DATA['year'] (None).

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

    name_tokens = re.split(r"[._]", weatherdata_name)
    period_in_name = next((k for k in period_map if k in name_tokens), None)

    if year is not None and period_in_name is not None:
        raise ValueError(
            "Ambiguous input: Provide either SITE_CONFIG_DATA['year'] OR valid weatherdata file and name including "
            "('p1', 'p2', 'p3') in WEATHERDATA_NAME - not both."
        )

    if year is None:
        if period_in_name is not None:
            return period_map[period_in_name]
        raise ValueError(
            "Missing year: WEATHERDATA_NAME must include 'p1', 'p2', or 'p3', "
            "or provide SITE_CONFIG_DATA['year'] manually."
        )

    if 2000 <= year <= 2500:
        warnings.warn(
            "Manual year provided. Ensure consistency with SITE_CONFIG_DATA['periods'].",
            UserWarning,
        )
        return year

    raise ValueError("SITE_CONFIG_DATA['year'] must be between 2000 and 2500.")


def extrapolate_to_blending_height(wind_speed_10m, roughness_length_freifeld, blending_height):
     """Extrapolate TRY 10 m wind speed to the blending height under freifeld assumptions.

     TRY wind_speed time series at 10 m are referenced to WMO standard exposure
     (open terrain / short grass, z0 ~ 0.03 m, no displacement height) rather than
     to the actual local urban surface. Combining this 10 m value directly with
     the local urban roughness_length (and a non-zero displacement height) in a
     single log-profile step is not valid here: since displacement_height (~16.57 m)
     exceeds the 10 m reference height, (10 - displacement_height) would be negative
     and the log-profile undefined.

     This function performs the first of two extrapolation stages (an Internal
     Boundary Layer / exposure-correction approach): 10 m (freifeld) -> blending
     height, using freifeld parameters only (roughness_length_freifeld, d=0). The
     second stage (blending height -> hub height, using the local urban
     roughness_length and displacement_height) is then carried out by windpowerlib's
     own logarithmic profile via MODELCHAIN_DATA['obstacle_height'].

     Source: WMO Guide to Meteorological Instruments and Methods of Observation;
     Wieringa, J. (1976), QJRMS; Zhao et al. (2022), Meteorological Applications,
     DOI: 10.1002/met.2094.

     Args:
         wind_speed_10m (pd.Series): Raw TRY wind speed at 10 m [m/s].
         roughness_length_freifeld (float): Freifeld roughness length [m], e.g. 0.03.
         blending_height (float): Target height for the first extrapolation stage [m].

     Returns:
         pd.Series: Wind speed extrapolated to blending_height [m/s].
     """
     return wind_speed_10m * (
         np.log(blending_height / roughness_length_freifeld)
         / np.log(10 / roughness_length_freifeld)
     )

def read_and_preprocess_weather_data(weatherdata_file):
    """Read and preprocess a TRY weather file into the windpowerlib MultiIndex format.

    Reads the semicolon-separated TRY file, selects the relevant columns, converts
    temperature from °C to Kelvin, adds a constant roughness-length column, and
    returns a DataFrame with a two-level column MultiIndex as expected by windpowerlib
    (see data/windpowerlib_weather.csv for the reference structure).

    The raw 10 m wind_speed is first extrapolated to SITE_CONFIG_DATA["blending_height"] under
    freifeld assumptions via extrapolate_to_blending_height() before being
    labeled with the local roughness_length. This accounts for the mismatch
    between the TRY reference exposure (open terrain) and the actual local
    urban displacement height (see MODELCHAIN_DATA['obstacle_height']).

    The calendar year is resolved automatically from the filename via resolve_year().
    Column names and measurement heights for the MultiIndex are taken from
    args['WEATHER_HEIGHTS_CONFIG'].

    Args:
        weatherdata_file (str | Path): Path to the TRY weather file (.txt, semicolon-separated).

    Returns:
        pd.DataFrame: Hourly time series indexed by a DatetimeIndex, with a
            MultiIndex column (variable_name, height). Contains pressure [Pa],
            temperature [K], wind speed [m/s], and roughness length [m].
    """
    year = resolve_year(weatherdata_file.name, RUN_CONFIG_DATA["year"])
    columns = ["pressure_surface", "wind_speed", "air_temperature_mean"]

    df = pd.read_csv(weatherdata_file, sep=";", usecols=columns)
    df = df.set_index(
        pd.date_range(start=f"1/1/{year}", periods=RUN_CONFIG_DATA["periods"], freq="h")
    )

    df = df.rename(
        columns={"pressure_surface": "pressure", "air_temperature_mean": "temperature"}
    )

    # Stage 1 of the two-stage extrapolation: 10 m (freifeld) -> SITE_CONFIG_DATA["blending_height"].
    # Stage 2 (SITE_CONFIG_DATA["blending_height"] -> hub_height, urban roughness/displacement) is
    # done by windpowerlib itself via MODELCHAIN_DATA['obstacle_height'].
    df["wind_speed"] = extrapolate_to_blending_height(
        df["wind_speed"], SITE_CONFIG_DATA["roughness_length_freifeld"], SITE_CONFIG_DATA["blending_height"]
    )

    df["roughness_length"] = SITE_CONFIG_DATA["roughness_length"]

    # transfer temperature from °C to Kelvin
    df["temperature"] = df["temperature"] + 273.15

    df = df[["pressure", "temperature", "wind_speed", "roughness_length"]]
    df.columns = pd.MultiIndex.from_tuples(
        WEATHER_COLUMNS, names=["column_name", "height"]
    )

    return df

def preprocess_nrel_turbine_model(nrel_turbine_model_path):
    columns = ["Wind Speed [m/s]", "Power [kW]"]
    power_curve_df = pd.read_csv(nrel_turbine_model_path, usecols=columns)
    power_curve_df = power_curve_df.rename(
        columns={
            "Wind Speed [m/s]": "wind_speed",
            "Power [kW]": "value"
        }
    )

    # convert power from kW to W
    power_curve_df["value"] = power_curve_df["value"] * 1000

    turbine_model = {
        "nominal_power": WIND_TURBINE_DATA["wind_turbine_nominal_power"],  # in W
        "hub_height": WIND_TURBINE_DATA["wind_turbine_hub_height"],  # in m
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


def run_windpowerlib(turbine_model, MODELCHAIN_DATA, weather_windpowerlib):
    """Run the windpowerlib ModelChain and return the turbine with power output.

    Args:
        turbine_model (dict): Turbine specification with keys 'nominal_power' [W],
            'hub_height' [m], and 'power_curve' (pd.DataFrame with 'wind_speed'
            and 'value' columns).
        MODELCHAIN_DATA (dict): ModelChain configuration (wind speed model,
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

    mc_my_turbine = ModelChain(my_turbine, **MODELCHAIN_DATA).run_model(
        weather_windpowerlib
    )
    # write power output time series to WindTurbine object
    my_turbine.power_output = mc_my_turbine.power_output

    return my_turbine


if __name__ == "__main__":
    input_files = []
    output_files = []

    turbine_model_path = (
        TURBINE_MODELS_NREL
        / WIND_TURBINE_DATA["wind_turbine_class"]
        / f"{WIND_TURBINE_DATA['wind_turbine_name']}.csv"
    )
    turbine_model = preprocess_nrel_turbine_model(turbine_model_path)

    for file in WEATHER_DATA_DIR.iterdir():
        if file.is_file() and file.suffix == ".csv" in file.name:
            input_files.append(file)

            weather_windpowerlib = read_and_preprocess_weather_data(file)

            my_turbine = run_windpowerlib(
                turbine_model, MODELCHAIN_DATA, weather_windpowerlib
            )

            wind_timeseries = my_turbine.power_output
            wind_timeseries_normalized = normalize_wind_timeseries(
                wind_timeseries, WIND_TURBINE_DATA["wind_turbine_nominal_power"]
            )

            wind_timeseries_normalized = rename_wind_timeseries(
                wind_timeseries_normalized, "wind_profile", "timeindex"
            )

            result_path = (
                RESULTS_DIR
                / f"wind_timeseries-{file.stem}-{wind_timeseries_normalized.index.year[0]}.csv"
            )
            wind_timeseries_normalized.to_csv(result_path)
            output_files.append(result_path)

    write_metadata(
        RESULTS_DIR,
        script=__file__,
        description="Normalized wind power time series computed from TRY weather data using windpowerlib ModelChain.",
        inputs=[turbine_model_path, *input_files],
        outputs=output_files,
        params={"run_config": RUN_CONFIG_DATA, "site_config": SITE_CONFIG_DATA, "wind_turbine": WIND_TURBINE_DATA,
                "modelchain": MODELCHAIN_DATA, "weather_columns": WEATHER_COLUMNS},
    )

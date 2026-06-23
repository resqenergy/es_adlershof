import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

import gsee.pv
import pandas as pd
import warnings

from settings import RAW_DIR, DATASETS_DIR

WEATHERDATA_DIR = RAW_DIR / "weather"
RESULTS_DIR = DATASETS_DIR / "gsee_timeseries"
RESULTS_DIR.mkdir(exist_ok=True)


args = {
    "year": None,
    "periods": 8760,
    "coords": (52.43, 13.54),  # coords of pv plant (52.43, 13.54) => Adlershof (Berlin)
    "tilt": [30, 90],  # 30 and 90 degrees tilt angle
    "azimut": [
        90,
        135,
        180,
        225,
        270,
    ],  # chosen azimut values to generate pv feed_in_timeseries [E,SE,S,SW,W]
    "capacity": 1,  # installed pv capacity [W]
}


def resolve_year(weatherdata_name, year=args["year"]):
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


def read_and_prepare_weatherdata(weatherdata_file, year, args=args):
    """
    Prepare input DataFrame for gsee.pv.run_model().

    ------------------------------
    - radiation_downwelling : global horizontal irradiance [W/m²]
    - radiation_diffuse     : diffuse irradiance component [W/m²]
    - air_temperature_mean  : ambient temperature [°C] (used by GSEE if provided)
    Returns
     -------
     pandas.DataFrame
        DataFrame indexed by time with columns:
        - global_horizontal
        - diffuse_fraction
        - temperature
    """

    columns = ["radiation_downwelling", "radiation_diffuse", "air_temperature_mean"]

    df_weatherdata = pd.read_csv(weatherdata_file, sep=";", usecols=columns)
    df_weatherdata.set_index(
        pd.date_range(start=f"1/1/{year}", periods=args["periods"], freq="H"),
        inplace=True,
    )

    df_weatherdata.rename(
        columns={
            "radiation_downwelling": "global_horizontal",
            "air_temperature_mean": "temperature",
        },
        inplace=True,
    )

    if (
        len(df_weatherdata[df_weatherdata["radiation_diffuse"] < 0])
        < args["periods"] * 0.05
    ):

        df_weatherdata["diffuse_fraction"] = (
            df_weatherdata["radiation_diffuse"] / df_weatherdata["global_horizontal"]
        ).fillna(0)

        df_weatherdata.loc[
            df_weatherdata["diffuse_fraction"] < 0, "diffuse_fraction"
        ] = 0.0

        # set diffuse_fraction = 0 where global_horizontal == 0
        mask_zero_ghi = df_weatherdata["global_horizontal"] == 0

        df_weatherdata.loc[mask_zero_ghi, "diffuse_fraction"] = 0.0

        df_weatherdata.drop(columns=["radiation_diffuse"], inplace=True)
    else:
        raise (
            ValueError,
            "Number of rows with negative diffuse_radiation increase the 5% treshhold. "
            "We recommend double-checking the TRY timeseries before you continue",
        )

    return df_weatherdata


def run_gsee(df_weatherdata, year, args=args):
    """
    Calculate PV feed-in time series for multiple azimuth angles using GSEE.#

    Uses configuration keys from `self.args`:
    - coords (lat, lon)
    - tilt (deg)
    - azimut (list[int]): azimuth angles passed to GSEE as `azim`
    - capacity (float): installed capacity (passed to GSEE, units follow GSEE conventions)
    - output_base_dir (str): base directory for CSV output
    - year (int): used for output filename only

    Returns
    -------
    pandas.DataFrame
        DataFrame with one column per azimuth (string column names),
        indexed by time. Values are PV feed-in from GSEE.
    """

    series_list = []
    header = []
    # pv_timeseries=pd.DataFrame()

    for tilt in args["tilt"]:
        for azim in args["azimut"]:
            # Run GSEE PV model for each azimuth.
            pv_feed_ts = gsee.pv.run_model(
                data=df_weatherdata,
                coords=args["coords"],
                tilt=tilt,
                azim=azim,
                tracking=0,
                capacity=args["capacity"],  # 1W
            )

            series_list.append(pv_feed_ts)
            header.append((tilt, azim))

    pv_timeseries = pd.concat(series_list, axis=1)
    pv_timeseries.columns = pd.MultiIndex.from_tuples(header, names=["tilt", "azimut"])

    return pv_timeseries


if __name__ == "__main__":

    for file in WEATHERDATA_DIR.iterdir():
        if file.is_file() and ".csv" in file.name:

            year = resolve_year(file.name)
            df_weatherdata = read_and_prepare_weatherdata(file, year)
            # Compute PV feed-in time series for all azimuth values and write CSV output
            gsee_timeseries = run_gsee(df_weatherdata, year)

            filename = file.name.split(".")
            result_path = RESULTS_DIR / f"gsee_timeseries-{filename[0]}-{year}.csv"
            gsee_timeseries.to_csv(result_path)

            print(f"Gsee timeseries successfully saved to: {result_path}")

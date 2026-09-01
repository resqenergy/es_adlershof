"""Get annual bev charging profiles consisting of local and commuter demand for the years 2025, 2035, and 2050 """

import pandas as pd
from settings import RAW_DIR, DATASETS_DIR
from utils.metadata import write_metadata

# =========================
# PATHS
# =========================
BEV_CHARGING_DIR = RAW_DIR / "bev_charging"

OUTPUT_DIR = DATASETS_DIR / "bev_charging_profiles"
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================
# Functions
# =========================
def get_bev_charging_timeseries(input_file, year):
    """
    This function reads the bev_charging input files and extracts
    the overall cumulative charging demand for electric vehicles.

    Parameters
    ----------
    input_file : str
        Path to the bev charging timeseries.

    year : str
        Respective year of the bev charging input file.

    Returns
    -------
    output_file : df
        Hourly resampled timeseries for electric vehicle demand.

    """
    BEV_CHARGING = pd.read_csv(input_file, header=3, sep=";", thousands=".")

    # Set timestep as index
    bev_ts = BEV_CHARGING.copy()
    bev_ts["timestamp"] = pd.to_datetime(bev_ts["timestamp"], format="%d.%m.%Y %H:%M")
    bev_ts = bev_ts.set_index("timestamp")

    # Extract total bev demand
    total_bev_ts = bev_ts[["Overall"]]

    # Resample quarter-hourly values to hourly demand
    total_bev_ts_resampled = total_bev_ts.resample("h").mean()
    total_bev_ts_hourly = total_bev_ts_resampled["Overall"]

    # create datetimeindex
    df_time = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    df = pd.DataFrame(
        {
            "timeindex": df_time,
            "bev_charging_cumulative_kW": total_bev_ts_hourly,
        }
    )
    output_file = OUTPUT_DIR / f"bev_charging_{year}_profile.csv"
    df.to_csv(output_file, index=False)

    return output_file


def extract_year(path) -> int:
    stem = path.stem
    candidates = [
        int(t)
        for t in stem.split("_")
        if t.isdigit() and len(t) == 4 and 2000 <= int(t) <= 2500
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"Expected exactly one year in filename, found {candidates}: {path.name}"
        )
    return candidates[0]


if __name__ == "__main__":
    input_files, output_files, years = [], [], []

    # get bev charging time series
    for _file in BEV_CHARGING_DIR.glob("*.csv"):
        _year = extract_year(_file)
        _output_file = get_bev_charging_timeseries(_file, _year)
        input_files.append(_file)
        output_files.append(_output_file)
        years.append(_year)

    write_metadata(
        OUTPUT_DIR,
        script=__file__,
        description="Hourly bev charging demand for technology park in Adlershof. Includes local and commuter demands.",
        inputs=input_files,
        outputs=output_files,
        params={"years": years},
    )

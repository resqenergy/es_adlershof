"""Module to generate COP timeseries for heatpumps."""

import pandas as pd

from settings import DATASETS_DIR, RAW_DIR
from utils.metadata import write_metadata

WEATHER_DIR = RAW_DIR / "weather"
TEMPERATURE_LOW_COLUMN = "temp_air"

RESULT_DIR = DATASETS_DIR / "heatpump_air"
RESULT_FILENAME = "ts_hp_air_cop.csv"
RESULT_COLUMN_NAME = "heatpump_air-profile"

QUALITY_GRADE = 0.4
KELVIN = 273.15

DEFAULT_REGION = "AD"
DEFAULT_YEAR = 2050
DEFAULT_TEMP_HIGH = 50.0


def calculate_cop(temp_low: pd.Series, temp_high: pd.Series) -> pd.Series:
    """Calculate COP for given temperatures."""
    temp_high_k = temp_high + KELVIN
    temp_low_k = temp_low + KELVIN
    cop = temp_high_k / (temp_high_k - temp_low_k) * QUALITY_GRADE
    cop.name = RESULT_COLUMN_NAME
    return cop


def get_temperature_low(region: str, year: int) -> pd.Series:
    """Read low temperature profile from file for given year."""

    filename = WEATHER_DIR / f"weatherdata_{region}_{year}.csv"
    if not filename.exists():
        error_msg = f"Could not find temperature profile file {filename}."
        raise FileNotFoundError(error_msg)

    temperature_low = pd.read_csv(filename)[TEMPERATURE_LOW_COLUMN]
    return temperature_low


if __name__ == "__main__":
    temp_low_series = get_temperature_low(region=DEFAULT_REGION, year=DEFAULT_YEAR)
    temp_high_series = pd.Series([DEFAULT_TEMP_HIGH] * len(temp_low_series))
    cop_series = calculate_cop(temp_low_series, temp_high_series)
    timeindex = pd.date_range(
        start=f"{DEFAULT_YEAR}-01-01", freq="h", periods=len(cop_series)
    )
    cop_series.index = timeindex
    cop_series.index.name = "timeindex"
    result_path = RESULT_DIR / RESULT_FILENAME
    cop_series.to_csv(result_path, sep=";", index=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    write_metadata(
        RESULT_DIR,
        script=__file__,
        description="Hourly COP time series for air-source heat pump, computed from ambient air temperature using a fixed quality grade.",
        inputs=[WEATHER_DIR / f"weatherdata_{DEFAULT_REGION}_{DEFAULT_YEAR}.csv"],
        outputs=[result_path],
        params={
            "region": DEFAULT_REGION,
            "year": DEFAULT_YEAR,
            "temp_high_C": DEFAULT_TEMP_HIGH,
            "quality_grade": QUALITY_GRADE,
        },
        sources=[],
    )

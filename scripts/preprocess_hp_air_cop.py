"""Module to generate air-source heatpump COP timeseries for all weather scenarios."""

from pathlib import Path

import pandas as pd

from settings import DATASETS_DIR, RAW_DIR
from utils.metadata import write_metadata
from utils.scenario import parse_weather_filename

WEATHER_DIR = RAW_DIR / "weather"
TEMPERATURE_LOW_COLUMN = "air_temperature_mean"

RESULT_DIR = DATASETS_DIR / "heatpump_air_cop"
RESULT_COLUMN_NAME = "heatpump_air-efficiency"

QUALITY_GRADE = 0.4
KELVIN = 273.15
TEMP_HIGH = 50.0  # in °C


def calculate_cop(temp_low: pd.Series, temp_high: float) -> pd.Series:
    """Calculate COP for given source and sink temperatures.

    Args:
        temp_low: Source (ambient air) temperature in °C.
        temp_high: Sink temperature in °C.

    Returns:
        COP time series.
    """
    temp_high_k = temp_high + KELVIN
    temp_low_k = temp_low + KELVIN
    cop = temp_high_k / (temp_high_k - temp_low_k) * QUALITY_GRADE
    cop.name = RESULT_COLUMN_NAME
    return cop


def calculate_cop_for_weather(weather_file: Path, scenario: str, year: int) -> None:
    """Calculate COP profile for one weather file and write CSV and metadata.

    Args:
        weather_file: TRY weather CSV file.
        scenario: Scenario name used in output filenames.
        year: Year used for the time index.
    """
    temp_low = pd.read_csv(weather_file, sep=";")[TEMPERATURE_LOW_COLUMN]
    cop = calculate_cop(temp_low, TEMP_HIGH)
    cop.index = pd.date_range(start=f"{year}-01-01", freq="h", periods=len(cop))
    cop.index.name = "timeindex"

    result_path = RESULT_DIR / f"cop_{scenario}.csv"
    cop.to_csv(result_path)
    write_metadata(
        RESULT_DIR,
        script=__file__,
        description="Hourly COP time series for air-source heat pump, computed from ambient air temperature using a fixed quality grade.",
        inputs=[weather_file],
        outputs=[result_path],
        params={
            "scenario": scenario,
            "year": year,
            "temp_high_C": TEMP_HIGH,
            "quality_grade": QUALITY_GRADE,
        },
        filename=f"cop_{scenario}.metadata.json",
        sources=[],
    )


if __name__ == "__main__":
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    for file in WEATHER_DIR.glob("*.csv"):
        weather_info = parse_weather_filename(file)
        if weather_info is None:
            continue
        # Same scenario naming as get_demands_per_building
        year_name = "statusquo" if weather_info.year == 2025 else str(weather_info.year)
        calculate_cop_for_weather(
            file, f"{year_name}_{weather_info.climate}", weather_info.year
        )

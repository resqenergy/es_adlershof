"""This module calculates COPs for different heat waste components."""

from __future__ import annotations

from io import StringIO

import requests
import pandas as pd

from settings import DATASETS_DIR

RESULT_DIR = DATASETS_DIR / "wasteheat_cop"
RESULT_DIR.mkdir(exist_ok=True)

KELVIN = 273.15
TARGET_TEMPERATURE = 88 + KELVIN  # in K

QUALITY_GRADE = 0.4


def calculate_cop(temp_target: float, temp_source: float | pd.Series):
    """Calculate COP for given temperature differences."""
    cop = QUALITY_GRADE * temp_target / (temp_target - temp_source)
    return cop


def calculate_heat_waste_cops(year: int):
    """Calculate COPs for heat waste components."""
    timeindex = pd.date_range(f"01-01-{year} 00:00:00", freq="h", periods=8760)

    # Read in canal temperature from Wasserportal Berlin
    response = requests.post(
        "https://wasserportal.berlin.de/station.php?anzeige=d&station=5866700&thema=owt",
        data={"sreihe": "ew", "smode": "c", "sdatum": "01.01.2025"},
    )
    canal_water_temperature_raw = pd.read_csv(
        StringIO(response.text),
        sep=";",
        decimal=",",
        index_col="Datum",
        parse_dates=True,
        date_format="%d.%m.%Y %H:%M",
        encoding="iso-8859-1",
    )
    canal_water_temperature = (
        canal_water_temperature_raw["Einzelwert"].resample("h").mean()[:8760]
    ) + KELVIN

    # Prepare winter/sommer temperatures for waste water
    jan_mar_temp = [(12 + 15) / 2 + KELVIN] * (31 + 28 + 31) * 24
    apr_sep_temp = [(17 + 20) / 2 + KELVIN] * (30 + 31 + 30 + 31 + 31 + 30) * 24
    oct_dec_temp = [(12 + 15) / 2 + KELVIN] * (31 + 30 + 31) * 24
    waste_water_temperature = pd.Series(
        jan_mar_temp + apr_sep_temp + oct_dec_temp, index=timeindex
    )

    TEMPERATURES = {
        "heatpump_office-efficiency": pd.Series([45 + KELVIN] * 8760),
        "heatpump_mt-efficiency": pd.Series([59 + KELVIN] * 8760),
        "heatpump_nt-efficiency": pd.Series([32 + KELVIN] * 8760),
        "heatpump_geothermal-efficiency": pd.Series([22 + KELVIN] * 8760),
        "heatpump_canal-efficiency": canal_water_temperature,
        "heatpump_wastewater-efficiency": waste_water_temperature,
    }

    cop_results = pd.DataFrame(
        {
            component: calculate_cop(TARGET_TEMPERATURE, temperatures).values
            for component, temperatures in TEMPERATURES.items()
        },
        index=timeindex,
    )

    result_file = RESULT_DIR / f"cop_{year}.csv"
    cop_results.to_csv(result_file, index_label="timeindex")


if __name__ == "__main__":
    import sys

    _year = int(sys.argv[1]) if len(sys.argv) > 1 else 2035
    calculate_heat_waste_cops(_year)

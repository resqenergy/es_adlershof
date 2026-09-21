"""Helpers for extracting scenario metadata from TRY weather filenames."""

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PERIOD_YEARS: dict[str, int] = {"p1": 2025, "p2": 2035, "p3": 2050}


@dataclass(frozen=True)
class WeatherFileInfo:
    """Metadata parsed from a TRY weather filename."""

    period: str
    year: int
    climate: str


def parse_weather_filename(
    path: Path, period_years: dict[str, int] | None = None
) -> WeatherFileInfo | None:
    """Extract period, year and climate scenario from a TRY weather filename.

    Expects the convention '<prefix>_<climate>.<period>.<ext>', e.g.
    'try_mean_rcp85.p1.csv'. Files that don't carry a recognized period key
    (such as reference datasets like 'npro_ref.csv') don't follow this
    convention and return None so callers can skip them.

    Args:
        path: Path to the weather file.
        period_years: Mapping from period key (e.g. 'p1') to calendar year.
            Defaults to DEFAULT_PERIOD_YEARS.

    Returns:
        Parsed metadata, or None if no recognized period key is found in the
        filename.
    """
    if period_years is None:
        period_years = DEFAULT_PERIOD_YEARS
    tokens = re.split(r"[._]", path.stem)
    period = next((token for token in tokens if token in period_years), None)
    if period is None:
        return None

    name_part = path.stem.split(".")[0]
    climate = name_part.split("_", 1)[1] if "_" in name_part else name_part
    return WeatherFileInfo(period=period, year=period_years[period], climate=climate)


if __name__ == "__main__":
    assert parse_weather_filename(Path("try_mean_rcp85.p1.csv")) == WeatherFileInfo(
        period="p1", year=2025, climate="mean_rcp85"
    )
    assert parse_weather_filename(Path("npro_ref.csv")) is None
    assert parse_weather_filename(
        Path("weather.reference.csv"), {"p1": 2020, "reference": 2011}
    ) == WeatherFileInfo(period="reference", year=2011, climate="weather")
    print("ok")

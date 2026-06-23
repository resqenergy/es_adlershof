"""Prepare PV timeseries for pv roof and facade models."""

import pandas as pd

from settings import RAW_DIR, DATASETS_DIR

PV_CONFIG_FILE = RAW_DIR / "pv_config" / "pv_config.csv"
GSEE_TIMESERIES_DIR = DATASETS_DIR / "gsee_timeseries"
RESULTS_DIR = DATASETS_DIR / "pv_profiles"
RESULTS_DIR.mkdir(exist_ok=True)


def calc_pv_feedin(gsee_timeseries_file):
    """
    Loads PV configuration and time-series data, calculates the weighted
    sum of feed-in per technology, and saves the results as a CSV file.

    Workflow:
    1. Load PV_CONFIG_FILE
    2. Load PV_TIMESERIES_FILE – timeseries data with MultiIndex columns
       (tilt, azimuth)
    3. For each technology, calculate the weighted sum of time series
       across all technologies
    4. Save the resulting DataFrame to RESULTS_FILE
    """

    pv_config = pd.read_csv(PV_CONFIG_FILE)

    gsee_timeseries = pd.read_csv(
        gsee_timeseries_file, header=[0, 1], parse_dates=True, index_col=0
    ).rename_axis("timeindex")
    gsee_timeseries.columns = gsee_timeseries.columns.set_levels(
        [pd.to_numeric(level) for level in gsee_timeseries.columns.levels]
    )

    pv_timeseries = pd.DataFrame()

    for technology, group in pv_config.groupby("technology"):
        ts = sum(
            gsee_timeseries[(row.tilt, row.azimuth)] * row.weight
            for _, row in group.iterrows()
        )
        pv_timeseries[technology] = ts

    return pv_timeseries


if __name__ == "__main__":
    for file in GSEE_TIMESERIES_DIR.iterdir():
        if file.is_file() and "gsee_timeseries" in file.name:

            pv_timeseries = calc_pv_feedin(file)

            filename = file.name.split("-")
            result_path = RESULTS_DIR / f"pv_timeseries-{filename[1]}-{filename[2]}"

            pv_timeseries.to_csv(result_path)

            print(f"PV timeseries successfully saved to: {result_path}")

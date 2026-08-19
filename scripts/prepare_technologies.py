import pandas as pd

from settings import RAW_DIR, DATASETS_DIR
from utils.metadata import write_metadata

TECHNOLOGIES_DIR = RAW_DIR / "technologies"
OUTPUT_DIR = DATASETS_DIR / "technologies"
OUTPUT_DIR.mkdir(exist_ok=True)

YEARS = (2025, 2035, 2050)


def melt_years_with_sources(parameter_df_raw: pd.DataFrame) -> pd.DataFrame:
    """Melt year value columns together with their matching source columns.

    Args:
        parameter_df_raw: Raw dataframe with one column per year (e.g. 2025)
            and one matching source column per year (e.g. source_2025).

    Returns:
        Long dataframe with year values gathered into "value" and their
        matching source columns gathered into "source". All other columns
        are kept as-is.
    """
    id_cols = [
        col
        for col in parameter_df_raw.columns
        if col not in YEARS and col not in {f"source_{year}" for year in YEARS}
    ]
    year_frames = [
        parameter_df_raw[[*id_cols, year, f"source_{year}"]]
        .rename(columns={year: "value", f"source_{year}": "source"})
        .assign(scenario=year)
        for year in YEARS
    ]
    return pd.concat(year_frames, ignore_index=True)


def transform_technologies() -> None:
    """Transform raw technology data into long format (unpacking scenario years)."""
    inputs, outputs = [], []
    for file in TECHNOLOGIES_DIR.glob("*.xlsx"):
        parameter_df_raw = pd.read_excel(file)
        parameter_df = melt_years_with_sources(parameter_df_raw)

        output_filename = OUTPUT_DIR / f"{file.stem}.csv"
        parameter_df.to_csv(output_filename, index=False, sep=";")

        inputs.append(file)
        outputs.append(output_filename)

    write_metadata(
        OUTPUT_DIR,
        script=__file__,
        inputs=inputs,
        outputs=outputs,
        description="Technology data.",
        params={},
    )


if __name__ == "__main__":
    transform_technologies()

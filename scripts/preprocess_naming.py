"""Preprocessing script to set name column in scalar files automatically."""

from pathlib import Path

import duckdb

PREPROCESSED_DIR = Path(__file__).parent.parent / "preprocessed"
PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR = Path(__file__).parent.parent / "raw"


def set_name_column(source: Path, target: Path):
    con = duckdb.connect(database=":memory:")
    con.execute(
        f"CREATE TABLE data_table AS SELECT * FROM read_csv_auto('{source}', sep=';', all_varchar=True) "
    )
    con.execute(
        "UPDATE data_table SET name = carrier || '-' || tech WHERE name IS NULL"
    )
    con.execute(
        f"COPY data_table TO '{target}' (HEADER, DELIMITER ';')",
    )


for file in (RAW_DIR / "scalars").iterdir():
    target_path = PREPROCESSED_DIR / "scalars" / file.name
    set_name_column(file, target_path)

set_name_column(
    RAW_DIR / "ts_load_electricity.csv", PREPROCESSED_DIR / "ts_load_electricity.csv"
)

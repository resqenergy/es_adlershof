import pandas as pd

from utils.files import read_file, write_file
from settings import RAW_DIR, RESULTS_DIR

# --------------------------------------------------
# Dateien laden
# --------------------------------------------------

companies_central_path = RAW_DIR / "companies_area_and_units_per_cluster_central.csv"
companies_decentral_path = (
    RAW_DIR / "companies_area_and_units_per_cluster_decentral.csv"
)
residents_central_path = RAW_DIR / "residents_area_and_units_per_cluster_central.csv"
residents_low_temp_central_path = (
    RAW_DIR / "residents_area_and_units_per_cluster_low_temp_central.csv"
)
residents_decentral_path = (
    RAW_DIR / "residents_area_and_units_per_cluster_decentral.csv"
)

companies_central = read_file(companies_central_path)
companies_decentral = read_file(companies_decentral_path)
residents_central = read_file(residents_central_path)
residents_low_temp_central = read_file(residents_low_temp_central_path)
residents_decentral = read_file(residents_decentral_path)

# --------------------------------------------------
# Funktionen zum Zusammenführen
# --------------------------------------------------


def merge_and_sum(df1, df2):
    merged = pd.concat([df1, df2])
    grouped = merged.groupby("Cluster", as_index=False).sum()
    return grouped


# --------------------------------------------------
# Daten zusammenführen
# --------------------------------------------------

# 1. central (Firmen + Bewohner)
total_central = merge_and_sum(companies_central, residents_central)

# 2. low temp central (nur Bewohner)
total_low_temp_central = residents_low_temp_central.copy()

# 3. dezentral (Firmen + Bewohner)
total_decentral = merge_and_sum(companies_decentral, residents_decentral)

# --------------------------------------------------
# Speichern
# --------------------------------------------------

write_file(
    total_central,
    RESULTS_DIR / "total_area_and_units_central.csv",
    index=False,
)
write_file(
    total_low_temp_central,
    RESULTS_DIR / "total_area_and_units_low_temp_central.csv",
    index=False,
)
write_file(
    total_decentral,
    RESULTS_DIR / "total_area_and_units_decentral.csv",
    index=False,
)

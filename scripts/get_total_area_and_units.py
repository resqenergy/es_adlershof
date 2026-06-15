import pandas as pd

from settings import RAW_DIR, DATASETS_DIR

CLUSTER_DIR = RAW_DIR / "cluster"
OUTPUT_DIR = DATASETS_DIR / "areas"
OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Dateien laden
# --------------------------------------------------

companies_central_path = (
    CLUSTER_DIR / "companies_area_and_units_per_cluster_central.csv"
)
companies_decentral_path = (
    CLUSTER_DIR / "companies_area_and_units_per_cluster_decentral.csv"
)
residents_central_path = (
    CLUSTER_DIR / "residents_area_and_units_per_cluster_central.csv"
)
residents_low_temp_central_path = (
    CLUSTER_DIR / "residents_area_and_units_per_cluster_low_temp_central.csv"
)
residents_decentral_path = (
    CLUSTER_DIR / "residents_area_and_units_per_cluster_decentral.csv"
)

companies_central = pd.read_csv(companies_central_path)
companies_decentral = pd.read_csv(companies_decentral_path)
residents_central = pd.read_csv(residents_central_path)
residents_low_temp_central = pd.read_csv(residents_low_temp_central_path)
residents_decentral = pd.read_csv(residents_decentral_path)

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

total_central.to_csv(
    OUTPUT_DIR / "total_area_and_units_central.csv",
    index=False,
)
total_low_temp_central.to_csv(
    OUTPUT_DIR / "total_area_and_units_low_temp_central.csv",
    index=False,
)
total_decentral.to_csv(
    OUTPUT_DIR / "total_area_and_units_decentral.csv",
    index=False,
)

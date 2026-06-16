"""Project floor area and unit counts per building cluster to 2035 and 2050 using Bebauungsplan growth factors."""

import pandas as pd

from settings import DATASETS_DIR
from utils.metadata import write_metadata

AREAS_DIR = DATASETS_DIR / "areas"
AREAS_FORECAST_DIR = DATASETS_DIR / "areas_forecast"
AREAS_FORECAST_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Dateien laden
# --------------------------------------------------

total_central_path = AREAS_DIR / "total_area_and_units_central.csv"
total_low_temp_central_path = AREAS_DIR / "total_area_and_units_low_temp_central.csv"
total_decentral_path = AREAS_DIR / "total_area_and_units_decentral.csv"

total_central = pd.read_csv(total_central_path, sep=",")
total_low_temp_central = pd.read_csv(total_low_temp_central_path, sep=",")
total_decentral = pd.read_csv(total_decentral_path, sep=",")

# --------------------------------------------------
# Cluster → Übercluster Mapping
# --------------------------------------------------

cluster_to_super = {
    "Alten-Pflegeheim": "Gewerbe",
    "Bibliothek": "Hochschule",
    "Büro": "Gewerbe",
    "Einfamilienhaus (1995–2001)": "Wohnen",
    "Einfamilienhaus (ab 2002)": "Wohnen",
    "Einkaufszentrum": "Gewerbe",
    "Einzelhandel": "Gewerbe",
    "Fitnesscenter": "Gewerbe",
    "Hotel": "Gewerbe",
    "Kantine": "Hochschule",
    "Kindergarten": "Gewerbe",
    "Krankenhaus": "Gewerbe",
    "Labor": "Forschung",
    "Lagerhalle": "Gewerbe",
    "Mehrfamilienhaus (ab 2002)": "Wohnen",
    "Parkhaus": "Gewerbe",
    "Produktion": "Gewerbe",
    "Rechenzentrum": "Medien",
    "Restaurant": "Gewerbe",
    "Schule": "Hochschule",
    "Sonstiges": "Gewerbe",
    "Sporthalle": "Gewerbe",
    "Supermarkt": "Gewerbe",
    "Theater": "Gewerbe",
}

# --------------------------------------------------
# Bebauungsplan Daten
# --------------------------------------------------

bebauung = pd.DataFrame(
    {
        "Übercluster": ["Gewerbe", "Wohnen", "Medien", "Forschung", "Hochschule"],
        "verfügbar": [5122822, 282444, 177007, 288891, 138247],
        "gebaut": [1314408, 280418, 135080, 139109, 91198],
    }
)

# Wachstumsfaktor berechnen
bebauung["wachstumsfaktor_2050"] = bebauung["verfügbar"] / bebauung["gebaut"]
bebauung["wachstum_rel"] = bebauung["wachstumsfaktor_2050"] - 1

wachstum_dict = dict(zip(bebauung["Übercluster"], bebauung["wachstum_rel"]))


# --------------------------------------------------
# Funktion zur Berechnung
# --------------------------------------------------


def apply_growth(df):
    df = df.copy()

    # Übercluster hinzufügen
    df["Übercluster"] = df["Cluster"].map(cluster_to_super)

    # Wachstum je Zeile bestimmen
    df["wachstum_rel"] = df["Übercluster"].map(wachstum_dict)

    # Falls etwas fehlt → 0 Wachstum
    df["wachstum_rel"] = df["wachstum_rel"].fillna(0)

    # 2035 = 25% Wachstum
    df["Nutzfläche_m2_2035"] = df["Nutzfläche_m2_statusquo"] * (
        1 + 0.25 * df["wachstum_rel"]
    )
    df["Nutzeinheiten_2035"] = (
        (df["Nutzeinheiten_statusquo"] * (1 + 0.25 * df["wachstum_rel"]))
        .round()
        .astype(int)
    )

    # 2050 = 60% Wachstum
    df["Nutzfläche_m2_2050"] = df["Nutzfläche_m2_statusquo"] * (
        1 + 0.6 * df["wachstum_rel"]
    )
    df["Nutzeinheiten_2050"] = (
        (df["Nutzeinheiten_statusquo"] * (1 + 0.6 * df["wachstum_rel"]))
        .round()
        .astype(int)
    )

    # --------------------------------------------------
    # 🔁 Umschichtung 2050: (1995–2001) → (ab 2002)
    # --------------------------------------------------

    old_mask = df["Cluster"].str.contains(r"\(1995–2001\)", regex=True, na=False)
    new_mask = df["Cluster"].str.contains(r"\(ab 2002\)", regex=True, na=False)

    if old_mask.any() and new_mask.any():
        # Werte aus alten Gebäuden (2050)
        add_area = df.loc[old_mask, "Nutzfläche_m2_2050"].sum()
        add_units = df.loc[old_mask, "Nutzeinheiten_2050"].sum()

        # Zu neuen Gebäuden addieren
        df.loc[new_mask, "Nutzfläche_m2_2050"] += add_area
        df.loc[new_mask, "Nutzeinheiten_2050"] += add_units

        # Alte Gebäude auf 0 setzen (nur 2050!)
        df.loc[old_mask, "Nutzfläche_m2_2050"] = 0
        df.loc[old_mask, "Nutzeinheiten_2050"] = 0

    return df.drop(columns=["wachstum_rel"])


# --------------------------------------------------
# Anwenden
# --------------------------------------------------

central_out = apply_growth(total_central)
low_temp_central_out = apply_growth(total_low_temp_central)
decentral_out = apply_growth(total_decentral)

# --------------------------------------------------
# Speichern
# --------------------------------------------------

central_out.to_csv(
    AREAS_FORECAST_DIR / "total_area_and_units_central_with_forecast.csv",
    index=False,
)
low_temp_central_out.to_csv(
    AREAS_FORECAST_DIR / "total_area_and_units_low_temp_central_with_forecast.csv",
    index=False,
)
decentral_out.to_csv(
    AREAS_FORECAST_DIR / "total_area_and_units_decentral_with_forecast.csv",
    index=False,
)
write_metadata(
    AREAS_FORECAST_DIR,
    script=__file__,
    description="Floor area and unit counts per building cluster with growth projections to 2035 and 2050, derived from Bebauungsplan data.",
    inputs=[total_central_path, total_low_temp_central_path, total_decentral_path],
    outputs=[
        AREAS_FORECAST_DIR / "total_area_and_units_central_with_forecast.csv",
        AREAS_FORECAST_DIR / "total_area_and_units_low_temp_central_with_forecast.csv",
        AREAS_FORECAST_DIR / "total_area_and_units_decentral_with_forecast.csv",
    ],
    params={
        "growth_fractions": {"2035": 0.25, "2050": 0.60},
        "bebauung": bebauung.to_dict(orient="records"),
    },
)

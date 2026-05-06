import requests
import pandas as pd
import os
from io import StringIO
from CoolProp.CoolProp import PropsSI

THIS_PATH = os.path.dirname(os.path.abspath(__file__))

years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

response = requests.post(
    "https://wasserportal.berlin.de/station.php?anzeige=d&station=5870100&thema=odf",
    data={"sreihe": "tw", "smode": "c", "sdatum": "01.01.2025"},
)
v_teltow = pd.read_csv(
    StringIO(response.text),
    sep=";",
    decimal=",",
    index_col="Datum",
    parse_dates=True,
    date_format="%d.%m.%Y",
    encoding="iso-8859-1",
)

response = requests.post(
    "https://wasserportal.berlin.de/station.php?anzeige=d&station=5866700&thema=owt",
    data={"sreihe": "tw", "smode": "c", "sdatum": "01.01.2025"},
)
t_teltow = pd.read_csv(
    StringIO(response.text),
    sep=";",
    decimal=",",
    index_col="Datum",
    parse_dates=True,
    date_format="%d.%m.%Y",
    encoding="iso-8859-1",
)

# Konstante Temperaturdifferenz
DELTA_T = 3.0  # °C

results = []

for year in years:
    # Jahresfilter
    t_year = t_teltow[t_teltow.index.year == year]
    v_year = v_teltow[v_teltow.index.year == year]

    if t_year.empty or v_year.empty:
        continue

    # Mittelwerte
    T_mean = t_year["Tagesmittelwert"].mean()  # °C
    V_mean = v_year["Tagesmittelwert"].mean()  # m³/s

    # Temperatur in Kelvin
    T_K = T_mean + 273.15

    # Stoffwerte Wasser
    rho = PropsSI("D", "T", T_K, "P", 101325, "Water")  # kg/m³
    cp = PropsSI("C", "T", T_K, "P", 101325, "Water")  # J/(kg·K)

    # Nutzwärmeleistung (W)
    Q_nutz_W = rho * cp * V_mean * DELTA_T

    # Umrechnung in MW
    Q_nutz_MW = Q_nutz_W / 1e6

    results.append(
        {
            "Jahr": year,
            "T_mean_°C": T_mean,
            "V_mean_m3s": V_mean,
            "rho_kgm3": rho,
            "cp_JkgK": cp,
            "Q_nutz_MW": Q_nutz_MW,
        }
    )

    # Ergebnisse als DataFrame
results_df = pd.DataFrame(results)

print(results_df)
print("")
print(f"Mittlere Nutzwärme: {round(results_df['Q_nutz_MW'].mean(), 0)}")

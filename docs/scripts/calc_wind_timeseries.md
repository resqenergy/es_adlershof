# Windleistungs-Zeitreihen berechnen

## Zweck

Berechnet normalisierte stündliche Windleistungs-Zeitreihen aus TRY-Wetterdaten (Testreferenzjahre) für jeden verfügbaren Klimapfad. Pro Wetterdatei entsteht eine normalisierte Zeitreihe (0–1), die direkt als `wind-profile` in oemof-tabular-Datenpakete eingebunden wird.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `raw/weather/*.csv` | TRY-Wetterdaten (semikolongetrennt), ein File pro Klimaszenario und Periode |
| `raw/wind_turbine_models/Distributed/2019COE_DW100_100kW_27.6.csv` | NREL-Leistungskurve der modellierten Windturbine |

Die TRY-Dateien enthalten stündliche Werte für Luftdruck (`pressure_surface`), Windgeschwindigkeit (`wind_speed`) und Lufttemperatur (`air_temperature_mean`). Der Messzeitraum wird aus dem Dateinamen abgeleitet:

| Dateinamen-Kürzel | Kalenderjahr |
|-------------------|-------------|
| `p1` | 2020 |
| `p2` | 2035 |
| `p3` | 2050 |
| `reference` | 2011 |

## Ausgaben

**Pfad:** `datasets/wind_profiles/wind_timeseries-{dateiname}-{jahr}.csv`

Pro TRY-Wetterdatei wird eine CSV-Datei erzeugt mit zwei Spalten:

| Spalte | Beschreibung |
|--------|-------------|
| `timeindex` | Stündlicher Zeitstempel |
| `wind_profile` | Normalisierte Windleistung \[0–1\] (gerundet auf 7 Dezimalstellen) |

## Parameter

Die wichtigsten Parameter sind im `args`-Dict sowie in `modelchain_data` am Skriptanfang definiert:

**Turbinen-Parameter (`args`):**

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `wind_turbine_name` | `2019COE_DW100_100kW_27.6` | NREL-Turbinenmodell |
| `wind_turbine_class` | `Distributed` | Turbinen-Klasse (Unterordner in `wind_turbine_models/`) |
| `wind_turbine_hub_height` | `40` m | Nabenhöhe |
| `wind_turbine_nominal_power` | `100000` W (100 kW) | Nennleistung zur Normierung |
| `coords` | `(52.43, 13.54)` | Koordinaten Adlershof (Berlin) |
| `roughness_length` | `0.6` m | Rauigkeitslänge des Geländes |
| `periods` | `8760` | Stunden pro Jahr |

**ModelChain-Parameter (`modelchain_data`):**

| Parameter | Wert |
|-----------|------|
| `wind_speed_model` | `logarithmic` |
| `density_model` | `barometric` |
| `temperature_model` | `linear_gradient` |
| `power_output_model` | `power_curve` |
| `density_correction` | `False` |

## Algorithmus

1. **Turbinen-Leistungskurve laden** — Die NREL-CSV wird eingelesen und von kW in W umgerechnet. Ein `WindTurbine`-Objekt wird initialisiert.
2. **Wetterdateien iterieren** — Alle `.csv`-Dateien in `raw/weather/` werden nacheinander verarbeitet.
3. **Wetterdaten vorverarbeiten** — Relevante Spalten werden ausgewählt, Temperatur von °C in Kelvin umgerechnet, eine konstante Rauigkeitslänge ergänzt und ein `MultiIndex`-DataFrame für windpowerlib erzeugt. Das Kalenderjahr wird aus dem Dateinamen (`p1`/`p2`/`p3`) abgeleitet.
4. **ModelChain ausführen** — windpowerlib's `ModelChain` berechnet die stündliche Leistungsabgabe der Turbine auf Basis von Windprofil, Dichte und Leistungskurve.
5. **Normieren** — Die Leistungsreihe wird durch die Nennleistung dividiert und auf 7 Stellen gerundet.
6. **Speichern** — Ausgabe als CSV mit `timeindex` und `wind_profile`.

## Abhängigkeiten

**windpowerlib** — Python-Bibliothek zur Simulation von Windkraftanlagen. Verwendet einen `ModelChain`-Ansatz: Wettervorverarbeitung → `WindTurbine`-Initialisierung → `ModelChain.run_model()` → Leistungsausgabe. Unterstützt verschiedene Windprofil-, Dichte- und Leistungsmodelle.

## Ausführung

Kein separates Makefile-Target vorhanden. Direktaufruf:

```bash
uv run -m scripts.calc_wind_timeseries
```

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

Das Kürzel wird als eigenständiges Token erkannt, der Dateiname wird dazu an `.` und `_` aufgetrennt (z. B. `rcp26.p3` oder `mean_reference`) — so wird ein Szenarioname wie `rcp26` nicht versehentlich als Kürzel `p2` erkannt.

## Ausgaben

**Pfad:** `datasets/wind_profiles/wind_timeseries-{dateiname}-{jahr}.csv`

Pro TRY-Wetterdatei wird eine CSV-Datei erzeugt mit zwei Spalten:

| Spalte | Beschreibung |
|--------|-------------|
| `timeindex` | Stündlicher Zeitstempel |
| `wind_profile` | Normalisierte Windleistung \[0–1\] (gerundet auf 7 Dezimalstellen) |

## Parameter

Die wichtigsten Parameter sind in vier Config-Dicts am Skriptanfang definiert:

**Run-Parameter (`RUN_CONFIG_DATA`):**

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `year` | `None` | Optionale explizite Vorgabe des Kalenderjahrs. Schließt sich mit einem Perioden-Kürzel (`p1`/`p2`/`p3`/`reference`) im Dateinamen gegenseitig aus |
| `periods` | `8760` | Stunden pro Jahr |

**Standort-Parameter (`SITE_CONFIG_DATA`):**

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `coords` | `(52.43, 13.54)` | Koordinaten Adlershof (Berlin) |
| `roughness_length` | `0.091` m | Lokale urbane Rauigkeitslänge (Quelle: TUB.Klima Messwerte, Median) |
| `roughness_length_freifeld` | `0.03` m | Freifeld-Rauigkeitslänge, passend zur TRY-Referenzexposition (WMO-Standard) |
| `displacement_height` | `16.57` m | Lokale urbane Verdrängungshöhe (Quelle: TUB.Klima Messwerte, Median) |
| `blending_height` | `60` m | Höhe, ab der die Windgeschwindigkeits-Extrapolation von Freifeld- auf lokale urbane Parameter umschaltet (siehe Algorithmus, Schritt 3) |

**Turbinen-Parameter (`WIND_TURBINE_DATA`):**

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `wind_turbine_name` | `2019COE_DW100_100kW_27.6` | NREL-Turbinenmodell |
| `wind_turbine_class` | `Distributed` | Turbinen-Klasse (Unterordner in `wind_turbine_models/`) |
| `wind_turbine_hub_height` | `40` m | Nabenhöhe |
| `wind_turbine_nominal_power` | `100000` W (100 kW) | Nennleistung zur Normierung |

**ModelChain-Parameter (`MODELCHAIN_DATA`):**

| Parameter | Wert |
|-----------|------|
| `wind_speed_model` | `logarithmic` |
| `density_model` | `barometric` |
| `temperature_model` | `linear_gradient` |
| `power_output_model` | `power_curve` |
| `density_correction` | `False` |
| `obstacle_height` | `displacement_height / 0.7` | so bestimmt, dass windpowerlibs intern verwendetes `d = 0.7 · obstacle_height` die gemessene `displacement_height` reproduziert |

## Algorithmus

1. **Turbinen-Leistungskurve laden** — Die NREL-CSV wird eingelesen und von kW in W umgerechnet. Ein `WindTurbine`-Objekt wird initialisiert.
2. **Wetterdateien iterieren** — Alle `.csv`-Dateien in `raw/weather/` werden nacheinander verarbeitet.
3. **Wetterdaten vorverarbeiten** — Relevante Spalten werden ausgewählt, Temperatur von °C in Kelvin umgerechnet, eine konstante Rauigkeitslänge ergänzt und ein `MultiIndex`-DataFrame für windpowerlib erzeugt. Das Kalenderjahr wird aus dem Dateinamen (`p1`/`p2`/`p3`/`reference`) abgeleitet.

   Die TRY-Windgeschwindigkeit wird in 10 m Höhe unter WMO-Freifeldexposition gemessen, nicht über der tatsächlichen lokalen urbanen Oberfläche. Sie kann daher nicht direkt mit der lokalen (urbanen) Rauigkeitslänge und Verdrängungshöhe auf Nabenhöhe extrapoliert werden: Da `displacement_height` (16,57 m) die 10 m Referenzhöhe übersteigt, wäre `10 − displacement_height` negativ und das logarithmische Profil undefiniert. Stattdessen wird eine zweistufige logarithmische Extrapolation verwendet:
      1. 10 m (Freifeld) → `blending_height` (60 m), ausschließlich mit Freifeld-Parametern (`roughness_length_freifeld`, ohne Verdrängungshöhe).
      2. `blending_height` → Nabenhöhe, durchgeführt von windpowerlibs eigenem logarithmischem Windprofil, unter Verwendung der lokalen urbanen `roughness_length` und `obstacle_height`.
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

# Normalisierte PV-Einspeise-Zeitreihen vorberechnen (GSEE)

## Zweck

Berechnet mit GSEE (Global Solar Energy Estimator) normalisierte stündliche PV-Einspeise-Zeitreihen — eine pro Montageausrichtung (Kombination aus Neigung und Azimut) — auf Basis von TRY-Wetterdaten. Die Ausgabe ist dimensionslos (eingespeiste W pro installiertem W) und dient als Ausgangsmaterial für `calc_pv_timeseries.py`, das diese Zeitreihen pro Ausrichtung später anhand der Flächenanteile aus `raw/pv_config/pv_config.csv` zu Zeitreihen pro Technologie (`pv_roof`, `pv_facade`) kombiniert.

> **Hinweis:** Dies ist ein einmaliger Vorberechnungsschritt. Für alle in diesem Projekt aktuell verwendeten Wetterszenarien wurden die normalisierten GSEE-Einspeiseprofile bereits erzeugt. Dieses Skript muss nur (erneut) ausgeführt werden, wenn ein neues Wetterszenario hinzukommt — andernfalls kann `calc_pv_timeseries.py` direkt mit den vorhandenen Dateien in `datasets/gsee_timeseries/` ausgeführt werden.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `raw/weather/*.csv` | TRY-Wetterdaten (semikolongetrennt), dieselben Dateien wie bei `calc_wind_timeseries.py` und `get_solar_thermal_profiles.py`. Verwendete Spalten: `radiation_downwelling`, `radiation_diffuse`, `air_temperature_mean` |

Das Kalenderjahr wird aus dem Dateinamen abgeleitet:

| Dateinamen-Kürzel | Kalenderjahr |
|-------------------|-------------|
| `p1` | 2020 |
| `p2` | 2035 |
| `p3` | 2050 |
| `reference` | 2011 (eigene Annahme eines historischen Referenzjahres) |

Alternativ kann ein Jahr manuell über `args["year"]` vorgegeben werden — jedoch nicht in Kombination mit einem Dateinamen, der ein Perioden-Kürzel enthält (löst `ValueError` aus, wenn beides oder keines von beidem angegeben wird).

## Ausgaben

**Pfad:** `datasets/gsee_timeseries/gsee_timeseries-{dateiname}-{jahr}.csv`

Pro TRY-Wetterdatei wird eine CSV-Datei erzeugt, indiziert über `timeindex`, mit einer Spalte pro `(tilt, azimuth)`-Kombination (MultiIndex-Spalten). Die Werte sind die normalisierte PV-Einspeisung (dimensionslos, eingespeiste W pro installiertem W).

## Parameter

Die Parameter sind im `args`-Dict am Skriptanfang definiert:

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `year` | `None` | Manuelle Übersteuerung des Kalenderjahres; auf `None` belassen, um es aus dem Dateinamen abzuleiten |
| `periods` | `8760` | Stunden pro Jahr |
| `coords` | `(52.43, 13.54)` | Koordinaten Adlershof (Berlin) |
| `tilt` | `[30, 90]` | Neigungswinkel in Grad — 30° für dachmontierte, 90° für fassadenmontierte PV |
| `azimut` | `[90, 135, 180, 225, 270]` | Azimutwinkel in Grad (O, SO, S, SW, W) |
| `capacity` | `1` | An GSEE übergebene installierte Leistung; bleibt bei 1 (dimensionslos W/W), damit die Ausgabe ein normalisierter Einspeiseanteil und keine absolute Leistung ist |

## Algorithmus

1. **Jahr auflösen** (`resolve_year`) — bestimmt das Kalenderjahr entweder aus `args["year"]` oder aus dem `p1`/`p2`/`p3`/`reference`-Kürzel im Dateinamen der Wetterdatei.
2. **Wetterdaten einlesen und vorbereiten** (`read_and_prepare_weatherdata`):
   - Auswahl von `radiation_downwelling`, `radiation_diffuse`, `air_temperature_mean` und Umbenennung in `global_horizontal`, `diffuse_fraction` (abgeleitet), `temperature`.
   - Aufbau eines stündlichen `DatetimeIndex` ab dem 1. Januar des aufgelösten Jahres.
   - Berechnung von `diffuse_fraction = radiation_diffuse / global_horizontal`, nach unten auf ≥ 0 begrenzt und auf 0 gesetzt, wo `global_horizontal == 0`.
   - Validierung: Enthalten mehr als 5 % der Zeilen einen negativen Wert für `radiation_diffuse`, soll die Funktion einen `ValueError` mit Hinweis auf eine manuelle Prüfung der TRY-Datei auslösen.
     > **Bekanntes Problem:** Die aktuelle Implementierung verwendet eine Python-2-artige Tuple-raise-Syntax (`raise (ValueError, "...")`), die in Python 3 keinen `ValueError` auslöst — stattdessen wird ein unzusammenhängender `TypeError` ausgelöst. Die Validierungsmeldung wird nie tatsächlich angezeigt. Als Fix vorgemerkt; im Rahmen dieser Dokumentation nicht behoben.
3. **GSEE ausführen** (`run_gsee`) — für jede Kombination aus `tilt` (2 Werte) und `azimut` (5 Werte) wird `gsee.pv.run_model(..., tracking=0, capacity=1)` aufgerufen (`tracking=0`: feste Montage, keine Nachführung) und die 10 resultierenden Zeitreihen werden zu einem DataFrame mit `(tilt, azimut)`-MultiIndex-Spalten zusammengeführt.
4. **Speichern** — eine Ausgabedatei pro Eingabe-Wetterdatei.

## Abhängigkeiten

**gsee** (`gsee.pv.run_model`) — der Kern der PV-Simulation. Das `gsee`-Paket (0.3.1) wird upstream nicht mehr gepflegt und unterstützt nur sehr alte Versionen von `numpy`/`pandas`/`pvlib-python`. Es muss daher in einer eigenen Legacy-Conda-Umgebung (`gsee37`, Python 3.7.12) statt in der normalen `uv`-Umgebung des Projekts ausgeführt werden — siehe `scripts/pv_precalc/environment.yaml`.

## Ausführung

Kein Aufruf über `uv` — dieses Skript benötigt die Conda-Umgebung `gsee37`:

```bash
$(conda info --base)/envs/gsee37/bin/python scripts/pv_precalc/calc_gsee_timeseries.py
```

Makefile-Target:

```bash
make gsee_timeseries
```

Dabei wird `GSEE_PYTHON` auf den Python-Interpreter der `gsee37`-Umgebung aufgelöst. Wie oben erwähnt handelt es sich um einen Vorberechnungsschritt, der für alle aktuell verwendeten Wetterszenarien bereits ausgeführt wurde — nur bei einem neuen Wetterszenario erneut ausführen.

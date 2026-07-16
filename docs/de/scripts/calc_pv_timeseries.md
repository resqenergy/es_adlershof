# PV-Einspeise-Zeitreihen zu Technologie-Profilen kombinieren

## Zweck

Kombiniert die normalisierten, nach Ausrichtung getrennten PV-Einspeise-Zeitreihen aus `calc_gsee_timeseries.py` zu je einer Zeitreihe pro PV-Technologie (`pv_roof`, `pv_facade`), gewichtet nach dem Flächenanteil jeder Ausrichtung an der installierten PV-Fläche. Dient als Quelle der Einspeiseprofile für die PV-Dach- und Fassadenmodelle im Energiesystemmodell.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `raw/pv_config/pv_config.csv` | Konfiguration der PV-Flächenanteile. Spalten: `technology` (`pv_roof`, `pv_facade`), `tilt` (Montage-Neigungswinkel in Grad), `azimuth` (Montage-Azimutwinkel in Grad), `weight` (Anteil der installierten PV-Fläche dieser Technologie bei dieser Neigung/Azimut). `weight` summiert sich pro Technologie über alle ihre Neigungs-/Azimut-Zeilen auf 1 |
| `datasets/gsee_timeseries/*gsee_timeseries*.csv` | Normalisierte PV-Einspeise-Zeitreihen pro `(tilt, azimuth)`, erzeugt von `calc_gsee_timeseries.py` |

> **Hinweis:** Jede in `pv_config.csv` referenzierte `(tilt, azimuth)`-Kombination muss als Spalte in der GSEE-Zeitreihendatei vorhanden sein, d. h. sie muss von `calc_gsee_timeseries.py`'s `args["tilt"]` / `args["azimut"]` abgedeckt sein (aktuell `tilt=[30, 90]`, `azimut=[90, 135, 180, 225, 270]`). Wird `pv_config.csv` um eine neue Neigung oder Azimut erweitert, ohne die GSEE-Zeitreihe dafür neu zu erzeugen, führt dies zu einem `KeyError`.

## Ausgaben

**Pfad:** `datasets/pv_profiles/pv_timeseries-{name}-{jahr}.csv`

Pro Eingabe-GSEE-Zeitreihendatei wird eine CSV-Datei erzeugt, indiziert über `timeindex`, mit einer Spalte pro Technologie (`pv_roof`, `pv_facade`).

## Parameter

Definiert als Pfad-Konstanten am Skriptanfang:

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `PV_CONFIG_FILE` | `raw/pv_config/pv_config.csv` | Konfiguration der PV-Flächenanteile |
| `GSEE_TIMESERIES_DIR` | `datasets/gsee_timeseries` | Eingabeverzeichnis, durchsucht nach Dateien, deren Name `"gsee_timeseries"` enthält |
| `RESULTS_DIR` | `datasets/pv_profiles` | Ausgabeverzeichnis |

## Algorithmus

1. **`calc_pv_feedin(gsee_timeseries_file)`**:
   - Lädt `pv_config.csv` sowie die übergebene GSEE-Zeitreihendatei (MultiIndex-Spalten `(tilt, azimuth)`, numerische Levels).
   - Gruppiert die Zeilen von `pv_config` nach `technology`. Für jede Technologie wird `gsee_timeseries[(tilt, azimuth)] * weight` über **alle** Zeilen der Gruppe summiert — dies unterstützt bereits mehrere unterschiedliche Neigungswinkel pro Technologie, nicht nur das aktuelle 1:1-Setup (`pv_roof` = 30°, `pv_facade` = 90°).
   - Ergebnis: eine Spalte pro Technologie.
2. **Hauptschleife** — für jede Datei in `GSEE_TIMESERIES_DIR`, deren Name `"gsee_timeseries"` enthält: `calc_pv_feedin` ausführen, Ausgabedateiname aus dem Eingabedateinamen ableiten (`gsee_timeseries-{name}-{jahr}.csv` → `pv_timeseries-{name}-{jahr}.csv`) und in `RESULTS_DIR` speichern.

## Abhängigkeiten

Keine externen Bibliotheken über den Projektstandard hinaus (pandas).

## Ausführung

```bash
make pv_timeseries
```

Entspricht: `uv run -m scripts.calc_pv_timeseries`

Läuft in der normalen `uv`-Umgebung des Projekts — anders als `calc_gsee_timeseries.py` wird hierfür nicht die Conda-Umgebung `gsee37` benötigt. Das `all`-Target im Makefile führt `gsee_timeseries` vor `pv_timeseries` aus, in der Praxis kann dieses Skript aber einfach gegen die bereits vorberechneten Dateien in `datasets/gsee_timeseries/` laufen (siehe [calc_gsee_timeseries.py-Dokumentation](calc_gsee_timeseries.md)), ohne den GSEE-Schritt erneut auszuführen.

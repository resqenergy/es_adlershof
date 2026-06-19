# NPRO-Gebäudesimulationen erstellen

## Zweck

Erstellt NPRO-Szenario-YAML-Dateien für alle Kombinationen aus Klimaszenario, Planungshorizont und Wärmenetzversorgungstopologie. Diese YAML-Dateien werden anschließend von der NPRO-Simulation ausgeführt, um stündliche Bedarfsprofile je Gebäudetyp zu berechnen.

## Eingaben

| Pfad | Inhalt |
|------|--------|
| `datasets/areas_forecast/total_area_and_units_central_with_forecast.csv` | Projizierte Flächen (zentral) |
| `datasets/areas_forecast/total_area_and_units_low_temp_central_with_forecast.csv` | Projizierte Flächen (Niedertemperatur) |
| `datasets/areas_forecast/total_area_and_units_decentral_with_forecast.csv` | Projizierte Flächen (dezentral) |
| `config/building_shares.yaml` | Anteile Bestand vs. Neubau je Planungshorizont |
| NPRO-Wetterdaten (`WEATHER_DIR`) | TRY-Wetterdateien, verwaltet durch npro |

### `config/building_shares.yaml`

Definiert den Anteil von Bestands- und Neubaugebäuden je Jahr für Nicht-Wohngebäude:

| Jahr | Bestand | Neubau |
|------|---------|--------|
| statusquo | 100 % | 0 % |
| 2035 | 83,38 % | 16,62 % |
| 2050 | 58,44 % | 41,56 % |

## Ausgaben

NPRO-Szenario-YAML-Dateien im NPRO-Szenarien-Verzeichnis (`SCENARIOS_DIR`, intern durch npro verwaltet), eine je Kombination aus Klimaszenario × Planungshorizont × Topologie. Dateiname-Schema:

```
{jahr}_{klimaszenario}_{topologie}.yaml
```

Beispiel: `2035_mean_rcp85_central.yaml`

Jede YAML-Datei enthält:

- `weather`: Dateiname der TRY-Wetterdatei
- `buildings`: Dictionary mit Gebäude-Schlüsseln und deren Parametern (`based_on`, `floorArea`, `numApart`, `buildingSubtype`, etc.)

## Parameter

| Parameter | Quelle | Bedeutung |
|-----------|--------|-----------|
| Planungshorizonte | Hard-kodiert | `statusquo`, `2035`, `2050` |
| Perioden-Mapping | Hard-kodiert | `p1`→statusquo, `p2`→2035, `p3`→2050 |
| Topologien | Hard-kodiert | `central`, `decentral`, `low_temp_central` |
| Anteile Bestand/Neubau | `config/building_shares.yaml` | Dynamisch je Jahr |

## Algorithmus

1. Iteriert über alle TRY-Wetterdateien im NPRO-Wetterverzeichnis.
2. Leitet Planungshorizont und Klimaszenario aus dem Dateinamen ab (Periodenkennzeichen `p1`/`p2`/`p3` und Klimabezeichnung).
3. Je Wetterdatei × Topologie-Kombination:
   - Lädt die projizierte Flächen-CSV für die entsprechende Topologie.
   - Für Wohngebäude wird ein einziger Eintrag mit Gesamtfläche und -einheiten erstellt (`numApart`, `shOption: heatLoad`).
   - Für Nicht-Wohngebäude wird die Anzahl Neubauten via `building_shares.yaml` berechnet. Bestands- und Neubau-Gebäude erhalten separate Einträge mit Suffix `_existing` bzw. `_new` und dem jeweiligen `buildingSubtype`.
   - Einträge mit 0 Nutzfläche oder 0 Neubaueinheiten werden übersprungen.
4. Schreibt das fertige Szenario als YAML-Datei in das NPRO-Szenarien-Verzeichnis.

## Abhängigkeiten

- **npro** (Git: [resqenergy/npro](https://github.com/resqenergy/npro)) — Gebäudeenergie-Simulationstool von ResQEnergy. Dieses Skript erzeugt die Eingabe-Szenarien für npro. Die eigentliche Simulation wird danach separat mit `npro run all` ausgeführt. npro ist als Git-Abhängigkeit in `pyproject.toml` eingetragen und stellt `SCENARIOS_DIR` und `WEATHER_DIR` bereit.
- **pandas** — Flächen-CSVs laden und verarbeiten.
- **PyYAML** — Szenario-YAML-Dateien schreiben.

## Ausführung

```bash
make npro_scenarios   # erstellt die NPRO-Szenario-YAML-Dateien
make npro_buildings   # führt die NPRO-Simulation aus (npro run all)
```

`make npro_buildings` setzt `make npro_scenarios` voraus. `make npro_scenarios` setzt `make areas_forecast` voraus.

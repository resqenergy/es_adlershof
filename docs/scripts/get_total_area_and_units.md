# Gebäudeflächen zusammenführen

## Zweck

Führt die Cluster-CSVs für Firmen und Bewohner zusammen und berechnet die gesamte Nutzfläche sowie die Nutzeinheiten je Gebäude-Cluster für die drei Wärmenetzversorgungstopologien `central`, `low_temp_central` und `decentral`.

## Eingaben

| Pfad | Inhalt |
|------|--------|
| `raw/cluster/companies_area_and_units_per_cluster_central.csv` | Nutzfläche und Einheiten der Firmengebäude (zentral) |
| `raw/cluster/companies_area_and_units_per_cluster_decentral.csv` | Nutzfläche und Einheiten der Firmengebäude (dezentral) |
| `raw/cluster/residents_area_and_units_per_cluster_central.csv` | Nutzfläche und Einheiten der Wohngebäude (zentral) |
| `raw/cluster/residents_area_and_units_per_cluster_low_temp_central.csv` | Nutzfläche und Einheiten der Wohngebäude (Niedertemperatur-Netz) |
| `raw/cluster/residents_area_and_units_per_cluster_decentral.csv` | Nutzfläche und Einheiten der Wohngebäude (dezentral) |

Alle Eingabedateien haben dieselbe Struktur:

| Spalte | Beschreibung |
|--------|-------------|
| `Cluster` | Gebäudetyp-Bezeichnung (z. B. „Büro", „Mehrfamilienhaus") |
| `Nutzfläche_m2_statusquo` | Nutzfläche im Status-quo \[m²\] |
| `Nutzeinheiten_statusquo` | Anzahl Nutzeinheiten im Status-quo |

## Ausgaben

Alle Ausgabedateien landen in `datasets/areas/` und haben dieselbe Struktur wie die Eingaben:

| Datei | Inhalt |
|-------|--------|
| `datasets/areas/total_area_and_units_central.csv` | Summe aus Firmen + Bewohnern (zentral) |
| `datasets/areas/total_area_and_units_low_temp_central.csv` | Nur Bewohner (Niedertemperatur-Netz) |
| `datasets/areas/total_area_and_units_decentral.csv` | Summe aus Firmen + Bewohnern (dezentral) |

## Parameter

Keine konfigurierbaren Parameter. Pfade sind im Skript fest definiert.

## Algorithmus

1. Lädt je Topologie die Firmen- und Bewohner-CSVs.
2. Fügt für `central` und `decentral` die Datensätze per `pd.concat` zusammen und summiert alle numerischen Spalten je `Cluster` mittels `groupby`.
3. Für `low_temp_central` werden nur die Bewohner-Daten übernommen (keine Firmengebäude in diesem Netz).
4. Speichert die drei zusammengeführten DataFrames als CSV.
5. Schreibt eine Metadatendatei via `utils.metadata.write_metadata`.

## Abhängigkeiten

- **pandas** — Daten einlesen, zusammenführen und speichern.

## Ausführung

```bash
make areas
```

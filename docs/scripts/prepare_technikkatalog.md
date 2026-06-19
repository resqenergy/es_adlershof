# Technikkatalog aufbereiten

## Zweck

Filtert und benennt Technologieparameter aus dem KWW-Technikkatalog um, sodass sie von oemof-pipe als Komponentenparameter eingelesen werden können. Erstellt eine bereinigte CSV mit Kosten- und Effizienzwerten für die im Modell verwendeten Wärmeversorgungstechnologien.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `raw/technikkatalog/KWW-Technikkatalog-Waermeplanung_12-2025(flatdata_all).csv` | Flachdaten-Export des Technikkatalogs (letztes Tabellenblatt `flatdata_all`), Semikolon-getrennt |

Der Eingabepfad wird in `utils/technikkatalog.py` als `FLATDATA_FILE_RAW` definiert.

## Ausgaben

| Pfad | Beschreibung |
|------|--------------|
| `datasets/technology_cost/kww_technikkatalog.csv` | Gefilterte und umbenannte Technologieparameter, Semikolon-getrennt, für oemof-pipe |

## Parameter

Das Mapping von Technikkatalog-Einträgen auf Modellkomponenten ist im Skript als `TECHNOLOGY_MAPPING` definiert:

| Technikkatalog-Bezeichnung | Kapazität \[MW\] | Modellname |
|---------------------------|----------------|------------|
| `AbwaermeWP_zentral` | 2 | `heatpump_office` |
| `AbwaermeWP_zentral` | 10 | `heatpump_nt` |
| `AbwaermeWP_zentral` | 20 | `heatpump_mt` |
| `BHKW_zentral` | 0.3 | `bhkw` |
| `Tiefengeothermie_ab400_direkt_zentral` | 10 | `heatpump_geothermal` |
| `AbwasserWP_zentral` | 10 | `heatpump_wastewater` |
| `GewaesserWP_zentral` | 10 | `heatpump_canal` |
| `Solarthermie_flach_dezentral` | 10 | `heat_decentral-solarthermal` |

Für neue Technologien: Mapping in `TECHNOLOGY_MAPPING` erweitern, dann Skript erneut ausführen.

## Algorithmus

1. `get_technology_data(TECHNOLOGY_MAPPING)` aus `utils/technikkatalog.py` aufrufen
2. Funktion liest Rohdaten, filtert nach den angegebenen Technologien und Kapazitäten
3. Spalten und Technologienamen werden gemäß Mapping auf oemof-pipe-konforme Bezeichnungen umbenannt
4. Ergebnis als Semikolon-CSV gespeichert

Das Skript enthält keine eigene Verarbeitungslogik — die gesamte Filterung und Umbenennung liegt in `utils/technikkatalog.py`.

## Abhängigkeiten

Keine externen Bibliotheken über den Projektstandard hinaus. Interne Abhängigkeit: `utils.technikkatalog` (enthält `Technology`, `get_technology_data`, `FLATDATA_FILE_RAW`).

**oemof-pipe**: Konsumiert die Ausgabedatei als Technologieparameter-Quelle für Blueprints.

## Ausführung

```bash
make parameters
```

Entspricht (erster Schritt): `uv run -m scripts.prepare_technikkatalog`

!!! note "Voraussetzung"
    Das letzte Tabellenblatt (`flatdata_all`) des Excel-Technikkatalogs muss vorab manuell als CSV exportiert und unter `raw/technikkatalog/` abgelegt werden.

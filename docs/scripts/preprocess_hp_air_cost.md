# Kosten für Luftwärmepumpen berechnen

## Zweck

Bestimmt Kapazitäten und gewichtete mittlere Kosten für dezentrale Luftwärmepumpen je Szenario. Kapazitäten werden aus NPRO-Gebäudewärmebedarfen und COP-Profilen abgeleitet; Kosten stammen aus dem Technikkatalog und werden nach Nutzeinheiten gewichtet.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `preprocessed/ts_hp_air_cop.csv` | Stündliche COP-Zeitreihe (Ausgabe von `preprocess_hp_air_cop.py`), Spalte `heatpump_air-profile` |
| `datasets/npro_buildings/<szenario>_<topologie>/` | NPRO-Gebäudeergebnisse je Szenario und Topologie (CSV mit `spaceHeatProfile`) |
| `datasets/areas_forecast/total_area_and_units_<topologie>_with_forecast.csv` | Nutzeinheiten je Cluster und Jahr |
| Technikkatalog-Rohdaten | Kosten für `LuftWP_dezentral` in Kapazitätsstufen 5–100 kW |

## Ausgaben

| Pfad | Beschreibung |
|------|--------------|
| `datasets/heatpump_air/heatpump_air_<szenario>.csv` | Kapazitäten und Kosten je Cluster, Topologie und Szenario |
| `datasets/heatpump_air/hp_cost.csv` | Gewichteter mittlerer Kostenparameter je Szenario (eine Zeile pro Szenario) |

Ausgabespalten je Szenariodatei: `Topology`, `Cluster`, `Nutzeinheiten`, `Available_Capacity`, sowie Kostenvariablen aus dem Technikkatalog.

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `TECHNIKKATALOG_HP_CAPACITIES` | `(5, 10, 20, 30, 40, 50, 60, 80, 100)` | Verfügbare WP-Kapazitätsstufen im Technikkatalog \[kW\] |
| `TECHNIKKATALOG_TECHNOLOGY_NAME` | `"LuftWP_dezentral"` | Technologiename im Technikkatalog |

## Algorithmus

**Kapazitätsberechnung je Cluster und Szenario:**

1. Für jede Kombination aus Szenario und Topologie (`central`, `decentral`, `low_temp_central`):
   - NPRO-Raumwärmebedarfe (`spaceHeatProfile`) je Cluster summieren
   - Mittleren Wärmebedarf pro Nutzeinheit berechnen
   - Spitzenlast als Maximum von `Wärmebedarf / COP` bestimmen
   - WP-Kapazität = 90 % der Spitzenlast

**Kostenzuordnung:**

2. Berechnete Kapazität auf nächstgelegene Technikkatalog-Kapazitätsstufe runden
3. Kosten für diese Kapazitätsstufe aus dem Technikkatalog abrufen

**Gewichtete Mittelung:**

4. Alle Cluster nach Nutzeinheiten gewichten → einen repräsentativen Kostenwert je Szenario erzeugen
5. Ergebnisse als CSV speichern

## Abhängigkeiten

Keine externen Bibliotheken über den Projektstandard hinaus. Interne Abhängigkeiten: `utils.technikkatalog` (Datenzugriff Technikkatalog), `utils.files` (CSV-Schreiben).

## Ausführung

```bash
uv run -m scripts.preprocess_hp_air_cost
```

Kein eigenständiges Makefile-Target. Muss nach `preprocess_hp_air_cop.py` ausgeführt werden.

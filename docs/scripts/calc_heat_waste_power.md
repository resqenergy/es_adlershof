# Abwärme-Kapazitäten berechnen

## Zweck

Leitet thermische Kapazitätspotenziale für alle Abwärme-Wärmepumpen-Komponenten ab. Unterschieden wird zwischen **dynamischen** Quellen (Kapazität aus Energieprofil × COP berechnet) und **statischen** Quellen (Kapazität direkt aus dem Technologie-Excel entnommen).

## Eingaben

| Pfad | Beschreibung |
|------|-------------|
| `raw/wasteheat_potentials/Abwärmepotenziale_Adlershof.xlsx` | Jahresenergien und Nennleistungen je Technologie und Planungshorizont |
| `datasets/wasteheat_cop/cop_{jahr}.csv` | Stündliche COP-Zeitreihen je Komponente |
| `datasets/wasteheat_profiles/{szenario}.csv` | Stündliche Energieprofile je Temperaturniveau |

## Ausgaben

**Pfad:** `datasets/wasteheat_capacity/capacity.csv`

| Spalte | Beschreibung |
|--------|-------------|
| `scenario` | Szenarioname (z.B. `2035_mean_rcp85`) |
| `name` | Komponenten-Bezeichnung (z.B. `heatpump_ht`) |
| `capacity_potential` | Thermische Kapazität \[kW\] |
| `full_load_time_max` | Volllaststunden (nur statische Quellen) \[h\] |

**Komponenten-Mapping:**

| Quelle (Excel) | Name (Ausgabe) |
|---------------|----------------|
| BTB-Abwärmerückgewinnung (Hochtemperatur) | `heatpump_ht` |
| Chemie + Industrie + BTB (Mitteltemperatur) | `heatpump_mt` |
| Wäscherei, Büro und Labor | `heatpump_office` |
| Rechenzentrum + BTB/Industrie (Niedertemperatur) | `heatpump_nt` |
| Abwasser *(statisch)* | `heatpump_wastewater` |
| Spree & Teltow-Kanal *(statisch)* | `heatpump_canal` |
| Geothermie mitteltief *(statisch)* | `heatpump_geothermal` |

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `PERCENTILE` | 95 | Perzentil zur Kapazitätsbestimmung aus Leistungsreihe |
| `YEAR_INDEX_LOOKUP` | `{2025: 0, 2035: 1, 2050: 2}` | Spaltenindex im Excel |
| `POWER_LOOKUP` | 7 | Zeilenindex der Nennleistung im Excel |
| Szenario | `2035_mean_rcp85` (hardcoded) | Zu verarbeitendes Szenario |
| Jahr | `2035` (hardcoded) | Planungshorizont |

## Algorithmus

**Dynamische Quellen (HT, MT, NT, Büro):**

1. Energieprofil und COP-Zeitreihe der Komponente laden.
2. Stündliche elektrische Leistung berechnen: `P_el = Energie / COP`.
3. Das 95. Perzentil der Leistungsreihe als Auslegungsleistung bestimmen.
4. Thermische Kapazität aus Auslegungsleistung × mittlerem COP berechnen.

**Statische Quellen (Abwasser, Kanal, Geothermie):**

1. Nennleistung direkt aus dem Excel-Datensatz lesen.
2. Volllaststunden aus Jahresenergie / Nennleistung berechnen.

Ergebnisse beider Gruppen werden zusammengeführt und als CSV gespeichert.

## Abhängigkeiten

**pandas** — Datenverarbeitung, Perzentil-Berechnung via `quantile()`.

**openpyxl** (transitiv über pandas) — Lesen der Excel-Quelldatei.

## Ausführung

```bash
make wasteheat_capacities
```

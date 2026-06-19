# Kapazitätskosten berechnen

## Zweck

Berechnet annualisierte Kapazitätskosten aus Overnight-CAPEX, Lebensdauer, WACC und fixen Betriebskosten. Verarbeitet zwei Eingabequellen: Wärmeversorgungstechnologien aus dem Technikkatalog sowie Solarthermie-Parameter.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `datasets/technology_cost/kww_technikkatalog.csv` | Gefilterte Technologiedaten (Ausgabe von `prepare_technikkatalog.py`) |
| `raw/solar_thermal/solar_thermal_parameters.csv` | Overnight-CAPEX, Lebensdauer und fixe Betriebskosten für Solarthermie |

Beide Dateien sind Semikolon-getrennte CSVs mit Spalten `scenario_key` (bzw. `scenario`), `name`, `var_name`, `var_value`.

## Ausgaben

| Pfad | Beschreibung |
|------|--------------|
| `datasets/technology_capacity_cost/kww_technikkatalog_capacity_cost.csv` | Annualisierte Kapazitätskosten für Wärmetechnologien, je Szenario und Technologie |
| `datasets/solar_thermal/solar_thermal_capacity_cost.csv` | Annualisierte Kapazitätskosten für Solarthermie |

Ausgabespalten: `scenario_key` (oder `scenario`), `name`, `capacity_cost`, optional `storage_capacity_cost`.

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `WACC` | 0.04 | Weighted Average Cost of Capital (4 %) |

Der WACC ist als Konstante im Skript definiert. Lifetime und CAPEX stammen aus den Eingabedateien.

## Algorithmus

Die Funktion `calculate_annual_cost` wird für beide Eingabedateien separat aufgerufen:

1. CSV einlesen; Zeilen mit `scenario_key == "ALL"` von der Berechnung ausschließen (werden durchgereicht)
2. Gruppierung nach `(scenario_key, name)`
3. Je Gruppe:
   - `lifetime` aus `var_name == "lifetime"` lesen
   - `capacity_cost_overnight` lesen → Annuität berechnen: `ann = CAPEX · WACC · (1+WACC)^n / ((1+WACC)^n − 1)`
   - `fixom_cost` addieren → `capacity_cost = ann + fixom`
   - Optional: gleiche Berechnung für `storage_capacity_cost_overnight`
4. Ergebnisse als DataFrame zusammenführen und als CSV speichern

Zeilen ohne `lifetime` oder ohne `capacity_cost_overnight` werden übersprungen.

## Abhängigkeiten

Keine externen Bibliotheken über den Projektstandard hinaus. Annuitätsberechnung in `utils.economics.annuity`.

**oemof-pipe**: Konsumiert beide Ausgabedateien als skalare Eingabedaten in den Szenario-YAMLs.

## Ausführung

```bash
make parameters
```

Entspricht (zweiter Schritt): `uv run -m scripts.preprocess_capacity_costs`

Muss nach `prepare_technikkatalog.py` ausgeführt werden, da `datasets/technology_cost/kww_technikkatalog.csv` als Eingabe benötigt wird.

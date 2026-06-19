# Flächenprognose nach Nutzungsart

## Zweck

Projiziert die Nutzflächen und Nutzeinheiten je Gebäude-Cluster auf die Planungshorizonte 2035 und 2050, basierend auf Wachstumsfaktoren aus dem Bebauungsplan. Zusätzlich wird für 2050 ein Umschichtungseffekt modelliert: Gebäude der Baualtersklasse 1995–2001 werden vollständig auf die Klasse „ab 2002" übertragen.

## Eingaben

| Pfad | Inhalt |
|------|--------|
| `datasets/areas/total_area_and_units_central.csv` | Zusammengeführte Flächen (zentral, Status-quo) |
| `datasets/areas/total_area_and_units_low_temp_central.csv` | Zusammengeführte Flächen (Niedertemperatur, Status-quo) |
| `datasets/areas/total_area_and_units_decentral.csv` | Zusammengeführte Flächen (dezentral, Status-quo) |

## Ausgaben

Alle Ausgabedateien landen in `datasets/areas_forecast/`:

| Datei | Inhalt |
|-------|--------|
| `total_area_and_units_central_with_forecast.csv` | Flächenprognose für zentrale Versorgung |
| `total_area_and_units_low_temp_central_with_forecast.csv` | Flächenprognose für Niedertemperatur-Netz |
| `total_area_and_units_decentral_with_forecast.csv` | Flächenprognose für dezentrale Versorgung |

Jede Ausgabedatei enthält gegenüber den Eingaben zusätzliche Spalten:

| Spalte | Beschreibung |
|--------|-------------|
| `Übercluster` | Oberkategorie des Clusters (z. B. „Gewerbe", „Wohnen") |
| `Nutzfläche_m2_2035` | Projizierte Nutzfläche für 2035 \[m²\] |
| `Nutzeinheiten_2035` | Projizierte Nutzeinheiten für 2035 |
| `Nutzfläche_m2_2050` | Projizierte Nutzfläche für 2050 \[m²\] |
| `Nutzeinheiten_2050` | Projizierte Nutzeinheiten für 2050 |

## Parameter

Die Wachstumsparameter sind direkt im Skript kodiert:

| Parameter | Wert | Bedeutung |
|-----------|------|-----------|
| Wachstumsanteil 2035 | 25 % des Gesamtwachstums | `Nutzfläche_statusquo * (1 + 0.25 * wachstum_rel)` |
| Wachstumsanteil 2050 | 60 % des Gesamtwachstums | `Nutzfläche_statusquo * (1 + 0.60 * wachstum_rel)` |

Bebauungsplan-Grunddaten (hart kodiert):

| Übercluster | Verfügbare Fläche \[m²\] | Gebaute Fläche \[m²\] |
|-------------|------------------------|----------------------|
| Gewerbe | 5 122 822 | 1 314 408 |
| Wohnen | 282 444 | 280 418 |
| Medien | 177 007 | 135 080 |
| Forschung | 288 891 | 139 109 |
| Hochschule | 138 247 | 91 198 |

## Algorithmus

1. Lädt die drei Flächen-CSVs aus `datasets/areas/`.
2. Berechnet je Übercluster den relativen Wachstumsfaktor: `verfügbar / gebaut - 1`.
3. Ordnet jedem Cluster über das `cluster_to_super`-Mapping einen Übercluster zu.
4. Berechnet die projizierten Flächen für 2035 (25 % des Wachstumspotenzials) und 2050 (60 % des Wachstumspotenzials).
5. Führt für 2050 eine Umschichtung durch: Fläche und Einheiten von Einfamilienhäusern der Baualtersklasse 1995–2001 werden auf die Klasse „ab 2002" addiert, da diese Gebäude bis 2050 modernisiert oder ersetzt worden sind. Die Werte der alten Klasse werden auf 0 gesetzt.
6. Speichert die drei projizierten DataFrames als CSV in `datasets/areas_forecast/`.

## Abhängigkeiten

- **pandas** — Daten laden, transformieren und speichern.

## Ausführung

```bash
make areas_forecast
```

Setzt `make areas` als vorherigen Schritt voraus.

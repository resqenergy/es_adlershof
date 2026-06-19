# Bedarfsprofile aggregieren

## Zweck

Aggregiert die stündlichen Bedarfsprofile aus den NPRO-Gebäudesimulationen je Szenario (Klimaszenario × Planungshorizont) und Topologie. Erzeugt normierte Stundenprofile (0–1) sowie eine Tabelle der Jahressummen je Bedarfsart, aufbereitet für die Weiterverwendung in oemof-pipe.

## Eingaben

| Pfad | Inhalt |
|------|--------|
| `datasets/npro_buildings/{szenario}/` | Je Szenario ein Verzeichnis mit einer CSV- und JSON-Datei pro Gebäude |

### Verzeichnisstruktur

```
datasets/npro_buildings/
└── 2035_mean_rcp85_central/
    ├── Büro_existing.csv
    ├── Büro_existing.json
    ├── ...
```

### Gebäude-CSV (Profildaten)

Jede Gebäude-CSV enthält stündliche Zeitreihen mit 8760 Zeilen. Verwendete Spalten:

| Spalte | Bedeutung |
|--------|-----------|
| `plugLoadsProfile` | Elektrischer Steckdosenbedarf \[kWh/h\] |
| `emobProfile` | Mobilitätsbedarf (E-Mobilität) \[kWh/h\] |
| `spaceHeatProfile` | Raumwärmebedarf \[kWh/h\] |
| `dhwProfile` | Warmwasserbedarf \[kWh/h\] |
| `spaceCoolProfile` | Raumkühlbedarf \[kWh/h\] |
| `processCoolProfile` | Prozesskältebedarf \[kWh/h\] |

### Gebäude-JSON (Metadaten)

Enthält u. a. `buildingType` (`residential` oder Nicht-Wohngebäude), um die Unterscheidung `residential` vs. `non_residential` zu ermitteln.

## Ausgaben

| Datei | Inhalt |
|-------|--------|
| `datasets/demand_profiles/total_demands.csv` | Jahressummen je Bedarfsart und Szenario, im Long-Format |
| `datasets/demand_profiles/{jahr}_{klimaszenario}.csv` | Normierte Stundenprofile (0–1) je Szenario |

### `total_demands.csv`

| Spalte | Beschreibung |
|--------|-------------|
| `year_climate` | Szenario-Schlüssel, z. B. `2035_mean_rcp85` |
| `name` | Bedarfsart-Bezeichnung, z. B. `electricity-residential-demand` |
| `amount` | Jahresenergie \[kWh\] |

### Normierte Stundenprofile

Spaltenbenennungskonvention:

- Wärme: `heat_{topologie}-{residential_type}` (z. B. `heat_central-residential`)
- Alle anderen: `{bedarfsart}-{residential_type}` (z. B. `electricity-non_residential`)

Zusätzlich enthält jede Profil-CSV eine `timeindex`-Spalte mit stündlichen Zeitstempeln.

## Parameter

| Parameter | Wert | Bedeutung |
|-----------|------|-----------|
| Zeitschritte | 8760 | Stündliche Auflösung (1 Jahr) |
| Bedarfsarten | electricity, mobility, heat, cool | Kombination aus den CSV-Profilen |
| Szenario-Ordner | Alle Unterordner in `datasets/npro_buildings/` | Automatisch erkannt |

Der Ordnername wird nach dem Schema `{jahr}_{klimaszenario}_{topologie}` geparst.

## Algorithmus

1. Iteriert über alle Szenario-Unterordner in `datasets/npro_buildings/`.
2. Leitet `jahr`, `klimaszenario` und `topologie` aus dem Ordnernamen ab.
3. Je Gebäude (JSON + CSV-Paar):
   - Liest das Gebäude-JSON, um `residential` vs. `non_residential` zu bestimmen.
   - Berechnet vier Bedarfsprofile: `electricity` (plugLoads), `mobility` (emob), `heat` (spaceHeat + dhw), `cool` (spaceCool + processCool).
   - Summiert die Profile auf die szenario-weiten Aggregate (Jahressummen und Stundenprofile).
4. Erstellt `total_demands.csv` im Long-Format (melt), mit dem Suffix `-demand` an den Spaltennamen.
5. Normiert die Stundenprofile durch Division mit den jeweiligen Jahressummen aus `total_demands.csv`.
6. Setzt einen `DatetimeIndex` (stündlich, ab 1. Januar des jeweiligen Jahres; für `statusquo` wird 2025 als Referenzjahr verwendet).
7. Speichert je Klimaszenario × Planungshorizont eine normierte Profil-CSV.

## Abhängigkeiten

- **pandas** — Profile laden, aggregieren, normieren und speichern.

## Ausführung

```bash
make demand_profiles
```

Setzt `make npro_buildings` voraus.

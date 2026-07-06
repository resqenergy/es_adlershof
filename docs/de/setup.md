# Einrichtung und Ausführung

## Installation

Das Projekt benötigt Python 3.13 oder neuer. Abhängigkeiten werden mit [uv](https://docs.astral.sh/uv/) verwaltet.

```bash
uv venv .venv
uv sync
```

Zwei Abhängigkeiten werden direkt aus Git installiert:

- **npro** — `https://github.com/resqenergy/npro`
- **oemof-pipe** — `https://github.com/rl-institut/oemof_pipe`

Die Quellen sind in `pyproject.toml` unter `[tool.uv.sources]` konfiguriert und werden von `uv sync` automatisch bezogen.

## Umgebungsvariablen

Die Skripte greifen auf einen S3-kompatiblen Objektspeicher (MinIO) zu. Die Zugangsdaten müssen in einer `.env`-Datei im Projektstamm hinterlegt werden:

```ini
MINIO_ENDPOINT=<endpunkt>
MINIO_ACCESS_KEY=<zugangsschlüssel>
MINIO_SECRET_KEY=<geheimschlüssel>
```

Die `.env`-Datei darf **nicht** in das Git-Repository eingecheckt werden (`.gitignore` beachten). `settings.py` lädt die Variablen automatisch via `python-dotenv`.

## Makefile-Pipeline

Das `Makefile` ist das zentrale Werkzeug zur Ausführung der Datenpipeline. Jedes Target entspricht einem Verarbeitungsschritt; Abhängigkeiten zwischen Targets sind im Makefile definiert und werden automatisch ausgeführt.

| Target | Beschreibung | Abhängigkeiten |
|---|---|---|
| `make areas` | Rohflächen und Nutzeinheiten je Cluster zusammenführen | — |
| `make areas_forecast` | Flächenprognose für 2035 und 2050 berechnen | `areas` |
| `make npro_scenarios` | NPRO-Szenario-YAMLs erstellen | `areas_forecast` |
| `make npro_buildings` | NPRO-Gebäudesimulationen ausführen (`npro run all`) | `npro_scenarios` |
| `make demand_profiles` | Bedarfsprofile aus NPRO-Ergebnissen aggregieren | `npro_buildings` |
| `make wasteheat_profiles` | Stündliche Abwärmeprofile berechnen | `demand_profiles` |
| `make wasteheat_cops` | COP-Zeitreihen für Abwärmepumpen berechnen | — |
| `make wasteheat_capacities` | Abwärmekapazitäten berechnen | — |
| `make solar_thermal` | Solarthermie-Profile berechnen | — |
| `make parameters` | Technikkatalog aufbereiten und Kapazitätskosten berechnen | — |
| `make datapackage` | Datenpaket via oemof-pipe erstellen (blueprint + scenario) | — |
| `make all` | `wasteheat_profiles`, `wasteheat_cops`, `areas_forecast`, `parameters`, `datapackage` | — |
| `make export_datapackage` | Fertiges Datenpaket zu S3 exportieren | — |

### Parameter

Mehrere Targets akzeptieren Makefile-Variablen:

- **`SCENARIO`** — Szenarioname (Standard: `2035_mean_rcp85`). Betrifft `wasteheat_profiles` und `datapackage`.
- **`YEAR`** — Zieljahr als Zahl (Standard: `2035`). Betrifft `wasteheat_profiles` und `wasteheat_cops`.

## Szenarien

Ein alternatives Szenario wird durch Übergabe des `SCENARIO`-Parameters erzeugt:

```bash
make datapackage SCENARIO=2050_mean_rcp85
make wasteheat_profiles SCENARIO=2050_mean_rcp85 YEAR=2050
```

Verfügbare Szenarien entsprechen den Ordnernamen in `datasets/npro_buildings/` und den Einträgen in `scenarios/`.

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

Das Skript zur Erstellung der Bedarfszeitreihen benötigt Zugangsdaten für das Tool NPRO.
Außerdem müssen die Pfade zu den Datenquellen definiert werden.
Dies geschieht am einfachtsten in einer `.env`-Datei im Projektordner:

```ini
NPRO_EMAIL=<user>
NPRO_PASSWORD=<password>
NPRO_PROJECT=2591-13-0

NPRO_SCENARIO_DIR=datasets/npro_scenarios
NPRO_WEATHER_DIR=raw/weather
NPRO_RESULT_DIR=datasets/npro_buildings
```

Die `.env`-Datei darf **nicht** in das Git-Repository eingecheckt werden (`.gitignore` beachten). `settings.py` lädt die Variablen automatisch via `python-dotenv`.

## Makefile-Pipeline

Das `Makefile` ist das zentrale Werkzeug zur Ausführung der Datenpipeline. 
Jedes Target entspricht einem Verarbeitungsschritt.
Um alle Schritte der Pipeline auszuführen, reicht es aus `make all` zu starten.

Abschließend kann das fertige datapackage mit `make export_datapackage` auf den S3 Speicher geladen werden.

Die Dokumentation des Projekts kann lokal mittels `make docs` erzeugt werden.

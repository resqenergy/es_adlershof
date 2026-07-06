# Solarthermie-Profile berechnen

## Zweck

Berechnet stündliche Wärmeleistungsprofile eines Flachkollektors für alle verfügbaren TRY-Wetterdatensätze. Die normalisierten Profile dienen als Einspeiseprofile für solarthermische Anlagen im Energiesystemmodell.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `<npro_weather_dir>/*.csv` | TRY-Wetterdaten (Stundenwerte, Semikolon-getrennt) mit Spalten `radiation_downwelling`, `radiation_diffuse`, `air_temperature_mean` |

Der Wetter-Ordner wird über `npro.settings.WEATHER_DIR` bestimmt.

## Ausgaben

| Pfad | Beschreibung |
|------|--------------|
| `datasets/solar_thermal_profiles/solar_thermal_profile_<wetterdatei>.csv` | Stündliche Wärmeleistung des Kollektors \[W/m²\], Spalte `solar_thermal_power`, Index `timeindex` |

Pro TRY-Wetterdatei wird eine separate Ausgabedatei erstellt. Periodenkennung (`p1`, `p2`, `p3`) im Dateinamen bestimmt das Zieljahr (2025, 2035, 2050).

## Parameter

Alle Parameter sind direkt im Skript als Konstanten definiert:

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `ETA_0` | 0.718 | Optischer Wirkungsgrad des Kollektors |
| `A1` | 3.89 | Thermischer Verlustkoeffizient 1. Ordnung \[W/(m²·K)\] |
| `A2` | 0.018 | Thermischer Verlustkoeffizient 2. Ordnung \[W/(m²·K²)\] |
| `TILT` | 0° | Neigungswinkel des Kollektors |
| `AZIMUT` | 20° | Azimutwinkel (Ost von Nord) |
| `TEMP_INLET` | 50 °C | Vorlauftemperatur des Kollektors |
| `LAT` | 52.43° | Breitengrad (Adlershof, Berlin) |
| `LONG` | 13.54° | Längengrad (Adlershof, Berlin) |

Kollektorkennwerte stammen aus dem Datenblatt eines Standardflachkollektors (Quelle: duurzaamloket.nl).

## Algorithmus

1. Für jede TRY-Wetterdatei im NPRO-Wetterordner:
   - Periodenkennung (`p1`/`p2`/`p3`) aus Dateiname extrahieren → Zieljahr bestimmen
   - Wetterdaten einlesen: Globalstrahlung, Diffusstrahlung, Lufttemperatur
   - Zeitindex als stündliche DatetimeIndex-Reihe des Zieljahres anlegen
2. Berechnung der Kollektorstrahlung auf der geneigten Fläche via pvlib:
   - Sonnenposition berechnen (`pvlib.solarposition.get_solarposition`)
   - Direkte Normalstrahlung (DNI) aus GHI und DHI ableiten
   - Gesamtstrahlung auf Kollektor (`poa_global`) berechnen
3. Kollektorwirkungsgrad nach EN 12975:
   - `η = η₀ − a₁·ΔT/E − a₂·ΔT²/E`
   - `ΔT = T_inlet + ΔT_n − T_amb`
   - Wirkungsgrad wird auf 0 begrenzt (kein negativer Ertrag)
4. Wärmeleistung: `Q = η · E_coll`
5. Ergebnis als CSV speichern

## Abhängigkeiten

**pvlib** (`pvlib>=0.15.1`): Berechnung von Sonnenposition, direkter Normalstrahlung und Gesamtbestrahlung auf der Kollektorfläche. Ersetzt manuelle geometrische Berechnungen.

**npro**: Liefert den Pfad zum Wetterordner (`npro.settings.WEATHER_DIR`), der die TRY-Eingabedaten enthält.

## Ausführung

```bash
make solar_thermal
```

Entspricht: `uv run -m scripts.get_solar_thermal_profiles`

# COP-Zeitreihen für Luftwärmepumpen

## Zweck

Berechnet eine stündliche COP-Zeitreihe für Luftwärmepumpen auf Basis von Außenlufttemperaturen und einer konstanten Vorlauftemperatur. Der COP wird nach dem Carnot-Ansatz mit festem Gütegrad bestimmt.

## Eingaben

| Pfad | Beschreibung |
|------|--------------|
| `raw/weather/weatherdata_<region>_<year>.csv` | Stündliche Wetterdaten mit Spalte `temp_air` (Außenlufttemperatur in °C) |

Standardmäßig: Region `AD` (Adlershof), Jahr `2050`.

## Ausgaben

| Pfad | Beschreibung |
|------|--------------|
| `datasets/heatpump_air/ts_hp_air_cop.csv` | Stündliche COP-Zeitreihe, Spalte `heatpump_air-profile`, Index `timeindex`, Semikolon-getrennt |

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `DEFAULT_REGION` | `"AD"` | Regionskürzel für Wetterdatei |
| `DEFAULT_YEAR` | `2050` | Referenzjahr |
| `DEFAULT_TEMP_HIGH` | `50.0 °C` | Vorlauftemperatur (Kondensatorseite) |
| `QUALITY_GRADE` | `0.4` | Gütegrad η (Verhältnis realer zu Carnot-COP) |
| `TEMPERATURE_LOW_COLUMN` | `"temp_air"` | Spaltenname in der Wetterdatei |

## Algorithmus

1. Außenlufttemperatur aus Wetterdatei einlesen (`temp_air` in °C)
2. Vorlauftemperatur als konstante Zeitreihe anlegen (50 °C)
3. COP nach Carnot-Formel mit Gütegrad:

$$\text{COP} = \frac{T_\text{high}}{T_\text{high} - T_\text{low}} \cdot \eta$$

   mit Temperaturen in Kelvin (°C + 273.15)
4. Zeitindex als stündliche DatetimeIndex-Reihe des Zieljahres anlegen
5. Ergebnis als Semikolon-CSV speichern

## Abhängigkeiten

Keine externen Bibliotheken über den Projektstandard hinaus (pandas, pathlib).

## Ausführung

```bash
uv run -m scripts.preprocess_hp_air_cop
```

Kein eigenständiges Makefile-Target. Wird als Vorverarbeitungsschritt vor `preprocess_hp_air_cost.py` benötigt.

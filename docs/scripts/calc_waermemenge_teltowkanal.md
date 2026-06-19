# Wärmemenge Teltow-Kanal abschätzen

## Zweck

Schätzt die mittlere nutzbare Wärmeleistung des Teltow-Kanals als Wärmequelle für Wärmepumpen. Dazu werden Durchfluss und Wassertemperatur jahresweise aus dem Wasserportal Berlin abgerufen und die thermisch nutzbare Leistung unter Annahme einer konstanten Temperaturdifferenz berechnet. Das Skript dient der Analyse und gibt Ergebnisse auf der Konsole aus.

## Eingaben

Alle Daten werden live per HTTP-POST vom Wasserportal Berlin abgerufen:

| Quelle | Station | Parameter |
|--------|---------|-----------|
| Wasserportal Berlin – Station 5870100 | Teltow-Kanal Schleuse Neukölln | Täglicher Durchfluss \[m³/s\] |
| Wasserportal Berlin – Station 5866700 | Teltow-Kanal | Tägliche Wassertemperatur \[°C\] |

Analysierte Jahre: 2017–2025.

## Ausgaben

Nur Konsolenausgabe (keine Dateien). Ausgegeben werden eine Ergebnistabelle sowie die mittlere Nutzwärmeleistung in MW:

| Spalte | Beschreibung |
|--------|-------------|
| `Jahr` | Kalenderjahr |
| `T_mean_°C` | Mittlere Wassertemperatur \[°C\] |
| `V_mean_m3s` | Mittlerer Durchfluss \[m³/s\] |
| `rho_kgm3` | Dichte des Wassers \[kg/m³\] |
| `cp_JkgK` | Spezifische Wärmekapazität \[J/(kg·K)\] |
| `Q_nutz_MW` | Nutzbare Wärmeleistung \[MW\] |

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `DELTA_T` | 3,0 °C | Angenommene nutzbare Temperaturdifferenz |
| `years` | 2017–2025 | Analysezeitraum |

## Algorithmus

1. **Daten abrufen** — Durchfluss und Temperatur werden per HTTP-POST vom Wasserportal Berlin geladen (täglich gemittelte Werte als CSV).
2. **Jahresweise verarbeiten** — Für jedes Jahr werden Jahres-Teilmengen aus den Tagesdaten gefiltert.
3. **Mittelwerte berechnen** — Mittlere Jahrestemperatur `T_mean` und mittlerer Durchfluss `V_mean`.
4. **Stoffwerte bestimmen** — CoolProp liefert temperaturabhängige Wasserdichte `ρ` und spezifische Wärmekapazität `cp` bei mittlerer Jahrestemperatur und Normaldruck (101325 Pa).
5. **Wärmeleistung berechnen:**

    $$Q_\text{nutz} = \rho \cdot c_p \cdot \dot{V} \cdot \Delta T$$

6. **Ausgabe** — Ergebnisse je Jahr sowie mittlere Nutzwärmeleistung über alle Jahre werden auf der Konsole ausgegeben.

## Abhängigkeiten

**CoolProp** — Thermodynamische Stoffwertbibliothek. Liefert über `PropsSI()` präzise temperaturabhängige Wasser-Eigenschaften (Dichte, Wärmekapazität) ohne tabellarisierte Näherungswerte.

**requests** — HTTP-POST-Anfragen an das Wasserportal Berlin. Benötigt Netzwerkzugang zur Laufzeit.

**pandas** — Zeitreihenverarbeitung, jahresweise Filterung.

## Ausführung

Kein Makefile-Target vorhanden. Direktaufruf:

```bash
uv run -m scripts.calc_waermemenge_teltowkanal
```

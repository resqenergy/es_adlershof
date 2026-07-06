# COP-Zeitreihen für Abwärme-Wärmepumpen

## Zweck

Berechnet stündliche COP-Zeitreihen (Coefficient of Performance) für sechs Abwärme-Wärmepumpen-Komponenten. Die Quelltemperaturen werden teils live vom Wasserportal Berlin abgerufen (Kanal), teils als saisonale Konstanten modelliert (Abwasser) oder als feste Jahreswerte angenommen (Büro, MT, NT, Geothermie).

## Eingaben

| Quelle | Beschreibung |
|--------|-------------|
| Wasserportal Berlin – Station 5866700 | Stündliche Wassertemperatur des Teltow-Kanals, live per HTTP-POST abgerufen |

Alle anderen Quelltemperaturen sind im Skript als Konstanten definiert (keine Eingabedateien).

## Ausgaben

**Pfad:** `datasets/wasteheat_cop/cop_{jahr}.csv`

| Spalte | Quelltemperatur | Beschreibung |
|--------|----------------|-------------|
| `timeindex` | – | Stündlicher Zeitstempel |
| `heatpump_office-efficiency` | 45 °C (konstant) | COP für Büro-Abwärme |
| `heatpump_mt-efficiency` | 59 °C (konstant) | COP für Mitteltemperatur-Abwärme |
| `heatpump_nt-efficiency` | 32 °C (konstant) | COP für Niedertemperatur-Abwärme |
| `heatpump_geothermal-efficiency` | 22 °C (konstant) | COP für Geothermie |
| `heatpump_canal-efficiency` | Live-Kanaldaten \[K\] | COP für Teltow-Kanal |
| `heatpump_wastewater-efficiency` | Saisonal: 13,5 °C / 18,5 °C | COP für Abwasser |

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `TARGET_TEMPERATURE` | 88 °C (361,15 K) | Vorlauftemperatur des Wärmenetzes |
| `QUALITY_GRADE` | 0,4 | Gütegrad (Carnot-Effizienzfaktor) |
| `YEAR` | z.B. `2035` | Kalenderjahr für Zeitindex und Abruf-Startdatum |

**Saisonale Abwassertemperaturen:**

| Monate | Temperatur |
|--------|-----------|
| Jan–Mär, Okt–Dez | 13,5 °C (Mittel aus 12–15 °C) |
| Apr–Sep | 18,5 °C (Mittel aus 17–20 °C) |

## Algorithmus

1. **Kanaldaten abrufen** — Per HTTP-POST an `wasserportal.berlin.de` (Station 5866700) werden stündliche Wassertemperaturen abgerufen, auf Stundenmittel resampled, auf 8760 Werte gekürzt und in Kelvin umgerechnet.
2. **Abwassertemperatur konstruieren** — Saisonale Temperatur-Arrays (Jan–Mär, Apr–Sep, Okt–Dez) werden zu einer 8760-stündigen Zeitreihe zusammengesetzt.
3. **Quelltemperaturen zusammenstellen** — Für alle sechs Komponenten werden Quelltemperaturen (konstant oder zeitabhängig) als `pd.Series` bereitgestellt.
4. **COP berechnen** — Für jede Komponente:

    $$\text{COP} = \eta_\text{Güte} \cdot \frac{T_\text{Ziel}}{T_\text{Ziel} - T_\text{Quelle}}$$

5. **Speichern** — Alle sechs COP-Reihen als CSV mit `timeindex`.

## Abhängigkeiten

**requests** — HTTP-POST-Anfragen an das Wasserportal Berlin. Benötigt Netzwerkzugang zur Laufzeit.

**pandas** — Zeitreihen-Resampling, DataFrame-Erstellung.

## Ausführung

```bash
make wasteheat_cops YEAR=2035
```

# Wärmetauscher LT ↔ HT

## Zweck

Berechnet die Nennleistungen der beiden Wärmetauscher zwischen dem Hochtemperatur-Netz (HT) und dem Niedertemperatur-Netz (LT) je Szenario sowie die stündliche Einspeisegrenze des Wärmetauschers LT → HT (Max-Profil). Die Ergebnisse gehen über die Szenario-Dateien in oemof-pipe ein.

## Hintergrund: Warum der Wärmetauscher LT → HT begrenzt wird

Das LT-Netz ist hydraulisch vom HT-Netz getrennt. Die Versorgung läuft über einen Wärmetauscher aus dem HT-Rücklauf (Richtung HT → LT). Umgekehrt kann Wärme aus dem LT-Netz, etwa ein Solarthermie-Überschuss, in den HT-Rücklauf eingespeist werden (Richtung LT → HT). Diese Richtung ist begrenzt.

**Grund:** Die Einspeisung erhöht die Rücklauftemperatur des HT-Netzes. Der Anstieg ist auf ΔT_RL,perm begrenzt, weil sonst die Erzeuger im HT-Netz an Effizienz verlieren und die Netzverluste steigen. (Hintergrund und Diskussion: [PR #20](https://github.com/resqenergy/es_adlershof/pull/20).)

**Herleitung:** Im HT-Netz gilt für den Wärmestrom an einem Zeitpunkt

$$Q_\text{HT} = \dot{m} \cdot c_p \cdot (T_\text{SUP,HT} - T_\text{RET,HT})$$

Die eingespeiste Wärme $Q_\text{LT→HT}$ hebt die Rücklauftemperatur um

$$\Delta T = \frac{Q_\text{LT→HT}}{\dot{m} \cdot c_p}$$

Mit $\Delta T = \Delta T_\text{RL,perm}$ folgt für die maximale Einspeisung

$$Q_\text{LT→HT} \le \alpha \cdot Q_\text{HT} \qquad \text{mit} \qquad \alpha = \frac{\Delta T_\text{RL,perm}}{T_\text{SUP,HT} - T_\text{RET,HT}}$$

**Folgen:**

- Die Grenze hängt von der HT-Last zum jeweiligen Zeitpunkt ab. Sie ist also zeitabhängig, nicht konstant.
- Die Nennleistung des Wärmetauschers ist $\alpha$ mal die HT-Spitzenlast. Das Max-Profil beschreibt den zeitlichen Verlauf als Anteil der HT-Last an der Spitze.
- Da $T_\text{SUP,HT} > T_\text{RET,HT}$ gilt, liegt $\alpha$ unter 1.
- Vereinfachungen: Netzverluste und die Auswirkung der Rücklaufauslastung auf die Erzeugerwirkungsgrade werden nicht modelliert.

## Eingaben

| Datei | Beschreibung |
|-------|-------------|
| `datasets/demand_profiles/{szenario}.csv` | Normierte stündliche Bedarfsprofile je Carrier (Summe je Carrier = 1), Spalte `timeindex` |
| `datasets/demand_profiles/total_demands.csv` | Jahresbedarfe je Szenario und Carrier in MWh (Spalten `year_climate`, `name`, `amount`) |

Verwendete Carrier:

- **HT-Last:** `heat_central-residential` und `heat_central-non_residential`
- **LT-Last:** `heat_lt_central-residential`

## Ausgaben

**Kapazitäten:** `datasets/heat_exchanger_capacity/capacity_{szenario}.csv` (Metadaten: `capacity_{szenario}.metadata.json`)

| Spalte | Beschreibung |
|--------|-------------|
| `scenario` | Szenarioname |
| `name` | `heat_central-heat_exchanger` (HT → LT) oder `heat_lt_central-heat_exchanger` (LT → HT) |
| `capacity` | Nennleistung in MW |

| `name` | Nennleistung |
|--------|-------------|
| `heat_central-heat_exchanger` | Spitze der LT-Last |
| `heat_lt_central-heat_exchanger` | $\alpha \cdot$ HT-Spitze |

**Max-Profil:** `datasets/heat_exchanger_max_profiles/max_{szenario}.csv` (Metadaten: `max_{szenario}.metadata.json`)

| Spalte | Beschreibung |
|--------|-------------|
| `timeindex` | Stündlicher Zeitstempel |
| `heat_lt_central-heat_exchanger-max` | HT-Last zur Stunde geteilt durch HT-Spitze (Wert zwischen 0 und 1, Maximum = 1) |

Zusammen mit der Nennleistung ergibt sich die maximale Einspeisung LT → HT zu jeder Stunde als $\alpha \cdot Q_\text{HT}(t)$.

Die Metadaten des Max-Profils werden zuletzt geschrieben. Das Makefile nutzt diese Datei als Fertigstellungsmarker.

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `T_SUP_HT` | 110 °C | Vorlauftemperatur des HT-Netzes (vorläufige Annahme) |
| `T_RET_HT` | 55 °C | Rücklauftemperatur des HT-Netzes (vorläufige Annahme) |
| `DELTA_T_RL_PERM` | 10 K | Zulässiger Anstieg der HT-Rücklauftemperatur durch Einspeisung (vorläufige Annahme) |
| `alpha` | ≈ 0,18 | Berechnet aus den drei Werten oben: 10 / (110 − 55) |


## Algorithmus

1. **Last berechnen** — Je Carrier wird die stündliche Last in MW gebildet: normiertes Profil × Jahresbedarf in MWh. Die Summe der Carrier ergibt die HT-Last und die LT-Last.
2. **Nennleistungen bestimmen** — HT → LT: Spitze der LT-Last. LT → HT: $\alpha$ × Spitze der HT-Last.
3. **Max-Profil bilden** — HT-Last je Stunde geteilt durch ihre Spitze.
4. **Speichern** — Kapazitäten und Max-Profil als CSV, jeweils mit Metadaten-Datei.

## Ausführung

```bash
make heat_exchangers SCENARIO=2035_mean_rcp85
```

Alternativ direkt:

```bash
uv run -m scripts.calc_heat_exchanger 2035_mean_rcp85
```

Die Tests liegen in `tests/test_calc_heat_exchanger.py`.

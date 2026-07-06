# Abwärme-Stundenprofile erzeugen

## Zweck

Disaggregiert jährliche Abwärmepotenziale in stündliche Profile je Temperaturniveau (HT/MT/NT/Büro). Die Zeitprofile werden aus nachfrageseitigen Wärme- und Kälteprofilen sowie quellenspezifischen Verfügbarkeitsfenstern abgeleitet und dann auf szenarioabhängige Jahresenergiesummen skaliert.

## Eingaben

| Pfad | Beschreibung |
|------|-------------|
| `raw/wasteheat_potentials/Abwaermepotenzial_Adlershof_BfEE.csv` | Abwärme-Quellen mit Temperaturbereichen, monatlichen Leistungsprofilen und Verfügbarkeiten je Quelle |
| `raw/wasteheat_potentials/Abwärmepotenziale_Adlershof.xlsx` | Jahresenergiesummen je Technologie und Planungshorizont (2025/2035/2050) in MWh |
| `datasets/demand_profiles/{szenario}.csv` | Normierte Stunden-Nachfrageprofile (Wärme, Kälte) für das gewählte Szenario |

## Ausgaben

**Pfad:** `datasets/wasteheat_profiles/{szenario}.csv`

| Spalte | Beschreibung |
|--------|-------------|
| `timeindex` | Stündlicher Zeitstempel |
| `heatpump_ht-low_temperature_potential` | Abwärme Hochtemperatur (≥90 °C) \[kWh/h\] |
| `heatpump_mt-low_temperature_potential` | Abwärme Mitteltemperatur (60–90 °C) \[kWh/h\] |
| `heatpump_nt-low_temperature_potential` | Abwärme Niedertemperatur (<60 °C) \[kWh/h\] |
| `heatpump_office-low_temperature_potential` | Abwärme Wäscherei/Büro/Labor \[kWh/h\] |

## Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `SCENARIO` | z.B. `2035_mean_rcp85` | Klimaszenario (Kommandozeilenargument) |
| `YEAR` | z.B. `2035` | Planungshorizont für Jahresenergiesummen (2025/2035/2050) |
| `YEAR_INDEX_LOOKUP` | `{2025: 0, 2035: 1, 2050: 2}` | Spaltenindex im Excel-Energiepotenzial |

**Temperaturniveau-Klassifikation:**

| Temperaturbereich | Niveau |
|-------------------|--------|
| ≥90 °C, 90–110 °C | HT |
| 60–90 °C | MT |
| sonst | NT |

**Quellspezifische Verfügbarkeitsfenster** (Auszug):

| Quelle | Stunden |
|--------|---------|
| Kälteanlage, NSHV, Druckluft, … | 0–24 h |
| iKWK Modul | 6–17 h |
| Glasmodul, KKM, RLT | 8–16 h |
| Kälte BFS 360 | 6–18 h |

## Algorithmus

1. **Rohdaten laden** — BfEE-CSV mit Abwärme-Quellen sowie Excel mit Jahresenergiesummen werden eingelesen und in Temperaturniveaus klassifiziert.
2. **Zeitindex aufbauen** — 8760-Stunden-DatetimeIndex für das gewählte Jahr wird erzeugt (Monat, Stunde, Wochentag).
3. **Nachfragebasierte Basisprofile** — Aus dem Nachfrageprofil des Szenarios werden normierte zentrale Wärme- und Kälteprofile abgeleitet: HT/MT nutzen das Wärmeprofil, NT das Kälteprofil.
4. **Quellenprofile berechnen** — Für jede Abwärme-Quelle:
   - Monatliche Gewichte aus dem Leistungsprofil berechnen.
   - Verfügbarkeitsmaske aus Tagesfenster und Wochenend-Kennzeichen erzeugen.
   - Pro Monat: Basisprofile × Verfügbarkeit × monatliche Gewichte → Stundenenergie.
5. **Aggregieren** — Profile aller Quellen je Temperaturniveau aufsummieren.
6. **Auf Jahresenergiesummen skalieren** — Aggregierte Profile werden auf die szenarioabhängigen Jahresenergiesummen aus dem Excel normiert und skaliert.
7. **Speichern** — Ausgabe als CSV mit `timeindex` und vier Leistungsspalten.

## Abhängigkeiten

**pandas / numpy** — Datenverarbeitung, Zeitreihenoperationen, Vektorisierung der Profilgenerierung.

## Ausführung

```bash
make wasteheat_profiles SCENARIO=2035_mean_rcp85 YEAR=2035
```

Szenario und Jahr sind anpassbar. Das Target setzt `demand_profiles` voraus.

# Energiesystem Adlershof – Dokumentation

Dieses Projekt erstellt oemof.tabular-Datenpakete für das Energiesystem des Stadtquartiers Adlershof (Berlin) im Rahmen des ResQEnergy-Projekts. Die Datenpakete bilden verschiedene Klimaszenarien (RCP 2.6, 4.5, 8.5) und Zeithorizonte (2035, 2050) ab und dienen als Eingabe für die Energiesystemoptimierung mit oemof.tabular.

## Datenpipeline

```mermaid
flowchart LR
    subgraph Rohdaten
        R1\[raw/cluster/\]
        R2\[raw/weather/\]
        R3[raw/wind_turbine_models/]
        R4[raw/solar_thermal/]
        R5[raw/wasteheat_potentials/]
        R6\[raw/technikkatalog/\]
    end

    subgraph Verarbeitungsschritte
        S1[get_total_area_and_units]
        S2[get_area_per_type_of_use_projection]
        S3[get_demands_per_building\nnpro]
        S4\[npro run all\]
        S5[get_demand_profiles]
        S6[get_waste_heat_profiles]
        S7[calc_heat_waste_cop]
        S8[calc_wind_timeseries\nwindpowerlib]
        S9[get_solar_thermal_profiles]
        S10[prepare_technikkatalog\npreprocess_capacity_costs]
        S11\[oemof-pipe blueprint\]
        S12\[oemof-pipe scenario\]
    end

    subgraph Zwischendaten
        D1\[datasets/areas/\]
        D2[datasets/areas_forecast/]
        D3\[npro Szenarien-YAMLs\]
        D4[datasets/npro_buildings/]
        D5[datasets/demand_profiles/]
        D6[datasets/wind_profiles/]
        D7[S3: wasteheat_profiles/]
        D8[S3: wasteheat_cop/]
        D9[S3: Parameter]
    end

    subgraph Ergebnisse
        E1\[datapackages/adlershof/\]
        E2[datapackages/adlershof_SCENARIO/]
    end

    R1 --> S1 --> D1
    D1 --> S2 --> D2
    D2 --> S3 --> D3
    D3 --> S4 --> D4
    D4 --> S5 --> D5
    D5 --> S6 --> D7
    R2 --> S7 --> D8
    R2 --> S8 --> D6
    R4 --> S9
    R5 --> S6
    R6 --> S10 --> D9
    D7 --> S11
    D8 --> S11
    D9 --> S11
    D6 --> S11
    S11 --> E1
    E1 --> S12 --> E2
```

## Einstieg

- [Einrichtung und Ausführung](setup.md) — Installation, Umgebungsvariablen, Makefile-Pipeline
- [Datenstrukturen](datenstrukturen.md) — Rohdaten (`raw/`), Zwischendaten (`datasets/`) und Datenpakete (`datapackages/`)
- [Skripte](scripts/) — Dokumentation aller Verarbeitungsschritte

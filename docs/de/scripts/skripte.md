# Skripte – Übersicht

Diese Seite gibt einen kurzen Überblick über alle Verarbeitungsskripte der Datenpipeline. Sie sind in drei Gruppen gegliedert: Skripte, die den **Energiebedarf** ermitteln, Skripte zur **Energieversorgung** (EE-Erzeugung und Abwärme) sowie Skripte für **technoökonomische Parameter** (Kosten- und Technologiedaten). Jede Zeile verlinkt auf die ausführliche Dokumentation des jeweiligen Skripts.

## Energiebedarfe

| Name | Skriptname (.py) | Beschreibung |
|------|-------------------|--------------|
| [Gebäudeflächen zusammenführen](get_total_area_and_units.md) | `get_total_area_and_units.py` | Führt Cluster-Daten zu Firmen und Bewohnern zusammen und berechnet Nutzfläche sowie Nutzeinheiten je Gebäude-Cluster und Versorgungstopologie. |
| [Flächenprognose](get_area_per_type_of_use_projection.md) | `get_area_per_type_of_use_projection.py` | Projiziert Nutzflächen und -einheiten je Cluster auf die Planungshorizonte 2035 und 2050 anhand von Wachstumsfaktoren aus dem Bebauungsplan. |
| [NPRO-Gebäudesimulationen](get_demands_per_building.md) | `get_demands_per_building.py` | Erstellt NPRO-Szenario-YAMLs für alle Kombinationen aus Klimaszenario, Planungshorizont und Topologie zur Berechnung stündlicher Gebäude-Bedarfsprofile. |
| [Bedarfsprofile aggregieren](get_demand_profiles.md) | `get_demand_profiles.py` | Aggregiert die stündlichen NPRO-Bedarfsprofile je Szenario und Topologie zu normierten Stundenprofilen und Jahressummen. |

## Energieversorgung: EE & Abwärme

| Name | Skriptname (.py) | Beschreibung |
|------|-------------------|--------------|
| [PV-Zeitreihen vorberechnen (GSEE)](calc_gsee_timeseries.md) | `scripts/pv_precalc/calc_gsee_timeseries.py` | Berechnet mit GSEE normalisierte stündliche PV-Einspeise-Zeitreihen je Montageausrichtung aus TRY-Wetterdaten. |
| [PV-Zeitreihen zu Technologie-Profilen](calc_pv_timeseries.md) | `calc_pv_timeseries.py` | Kombiniert die GSEE-Ausrichtungsprofile flächengewichtet zu je einer Zeitreihe pro PV-Technologie (Dach/Fassade). |
| [Windleistungs-Zeitreihen](calc_wind_timeseries.md) | `calc_wind_timeseries.py` | Berechnet normalisierte stündliche Windleistungs-Zeitreihen aus TRY-Wetterdaten für jeden Klimapfad. |
| [Solarthermie-Profile](get_solar_thermal_profiles.md) | `get_solar_thermal_profiles.py` | Berechnet stündliche Wärmeleistungsprofile eines Flachkollektors für alle TRY-Wetterdatensätze. |
| [Abwärme-Stundenprofile](get_waste_heat_profiles.md) | `get_waste_heat_profiles.py` | Disaggregiert jährliche Abwärmepotenziale in stündliche Profile je Temperaturniveau. |
| [COP Abwärme-WP](calc_heat_waste_cop.md) | `calc_heat_waste_cop.py` | Berechnet stündliche COP-Zeitreihen für sechs Abwärme-Wärmepumpen-Komponenten anhand ihrer Quelltemperaturen. |
| [Abwärme-Kapazitäten](calc_heat_waste_power.md) | `calc_heat_waste_power.py` | Leitet thermische Kapazitätspotenziale für alle Abwärme-Wärmepumpen-Komponenten ab. |
| [Teltow-Kanal Wärmemenge](calc_waermemenge_teltowkanal.md) | `calc_waermemenge_teltowkanal.py` | Schätzt die mittlere nutzbare Wärmeleistung des Teltow-Kanals als Wärmepumpen-Quelle aus Durchfluss- und Temperaturdaten. |
| [COP Luftwärmepumpen](preprocess_hp_air_cop.md) | `preprocess_hp_air_cop.py` | Berechnet eine stündliche COP-Zeitreihe für Luftwärmepumpen nach dem Carnot-Ansatz. |

## Technoökonomische Parameter

| Name | Skriptname (.py) | Beschreibung |
|------|-------------------|--------------|
| [Technikkatalog aufbereiten](prepare_technikkatalog.md) | `prepare_technikkatalog.py` | Filtert und benennt Technologieparameter aus dem KWW-Technikkatalog für die Nutzung in oemof-pipe um. |
| [Kapazitätskosten](preprocess_capacity_costs.md) | `preprocess_capacity_costs.py` | Berechnet annualisierte Kapazitätskosten aus CAPEX, Lebensdauer, WACC und Betriebskosten für Wärmetechnologien und Solarthermie. |
| [Kosten Luftwärmepumpen](preprocess_hp_air_cost.md) | `preprocess_hp_air_cost.py` | Bestimmt Kapazitäten und gewichtete mittlere Kosten für dezentrale Luftwärmepumpen je Szenario. |

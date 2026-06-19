# Datenstrukturen

## Rohdaten (raw/)

Der Ordner `raw/` enthält alle Eingangsdaten, die manuell bereitgestellt werden müssen. Sie werden von keinem Skript erzeugt und bilden den Ausgangspunkt der Datenpipeline.

### raw/cluster/

Dieser Ordner enthält CSV-Dateien mit Nutzflächen (m²) und Nutzeinheiten pro Gebäudecluster, getrennt nach Unternehmensgebäuden und Wohngebäuden sowie nach Wärmeversorgungstopologien. Die Topologien `central`, `decentral` und `low_temp_central` entsprechen den drei modellierten Wärmenetzszenarien für das Quartier Adlershof.

Dateien:

- `companies_area_and_units_per_cluster_central.csv`
- `companies_area_and_units_per_cluster_decentral.csv`
- `residents_area_and_units_per_cluster_central.csv`
- `residents_area_and_units_per_cluster_decentral.csv`
- `residents_area_and_units_per_cluster_low_temp_central.csv`

Diese Dateien sind die primäre Datengrundlage für `get_total_area_and_units.py` und damit der Ausgangspunkt der gesamten Bedarfsberechnung.

### raw/weather/

Testreferenzjahre (TRY) des Deutschen Wetterdienstes (DWD) für den Standort Berlin Adlershof. Die Dateien sind semikolongetrennte CSV-Dateien und enthalten stündliche Wetterdaten für ein vollständiges Jahr (8760 Stunden): Luftdruck an der Oberfläche, mittlere Lufttemperatur und Windgeschwindigkeit in 10 m Höhe.

Die Dateinamen folgen dem Schema `try_{klimaszenario}.{periode}.csv`, wobei die Periode den Zeithorizont kodiert:

- `p1` → Jahr 2020 (nahe Zukunft)
- `p2` → Jahr 2035 (mittlere Zukunft)
- `p3` → Jahr 2050 (ferne Zukunft)

Verfügbare Klimaszenarien: `mean_rcp26`, `mean_rcp45`, `mean_rcp85`, `extr1_rcp85`, `extr2_rcp85`, `extr3_rcp85`. Die `extr`-Varianten repräsentieren Extremjahre innerhalb des RCP-8.5-Szenarios.

Eine `datapackage.json` beschreibt die Ressourcen nach dem Frictionless-Standard.

Die Wetterdaten werden von `calc_wind_timeseries.py`, `calc_heat_waste_cop.py` und `get_solar_thermal_profiles.py` genutzt.

### raw/wind_turbine_models/

Leistungskurven von Kleinwindanlagen aus dem NREL Turbine Models Datensatz. Die Dateien sind im Unterordner `Distributed/` abgelegt und repräsentieren Anlagen der Klasse „Distributed" (dezentrale Kleinanlagen bis ca. 1 MW).

Jede CSV-Datei enthält zwei Spalten: `Wind Speed \[m/s\]` und `Power \[kW\]`. Der Dateiname kodiert Hersteller, Modell, Nennleistung und Rotordurchmesser. Das Modell `2019COE_DW100_100kW_27.6` wird als Standard-Windenergieanlage in `calc_wind_timeseries.py` verwendet.

### raw/solar_thermal/

Parameterdatei für Solarthermie-Kollektoren (`solar_thermal_parameters.csv`). Enthält die technischen Kennwerte der modellierten Kollektoren (z. B. optischer Wirkungsgrad, Wärmedurchgangskoeffizient), die als Grundlage für die Berechnung stündlicher Solarthermie-Ertragsprofile in `get_solar_thermal_profiles.py` dienen.

### raw/wasteheat_potentials/

Abwärmepotenziale für den Standort Adlershof aus verschiedenen Quellen:

- `Abwaermepotenzial_Adlershof_BfEE.csv` — Erhebung des Bundesamts für Wirtschaft und Ausfuhrkontrolle (BfEE) zu industriellen Abwärmepotenzialen, aufgeschlüsselt nach Temperaturklassen (Hochtemperatur HT, Mitteltemperatur MT, Niedertemperatur NT, Büroanwendungen).
- `Abwärmepotenziale_Adlershof.xlsx` — Ergänzende Abwärmepotenziale aus weiteren Quellen.
- `wassertemperatur_schleuse_neukoelln.csv` — Gemessene Wassertemperaturen an der Schleuse Neukölln (Teltow-Kanal). Grundlage für die Berechnung der nutzbaren Wärmeleistung aus dem Teltow-Kanal in `calc_waermemenge_teltowkanal.py`.

### raw/technikkatalog/

Der KWW-Technikkatalog Wärmeplanung (Stand Dezember 2025) als flache CSV-Datei (`KWW-Technikkatalog-Waermeplanung_12-2025(flatdata_all).csv`). Das Original-Excel enthält mehrere Tabellenblätter; die hier vorliegende CSV entspricht dem exportierten `flatdata_all`-Blatt.

Der Technikkatalog enthält Kosten- und Effizienzparameter (Investitionskosten, Betriebskosten, Wirkungsgrade, Lebensdauern) für alle im Energiesystemmodell verwendeten Technologien. Er wird von `prepare_technikkatalog.py` eingelesen und in das oemof-pipe-Eingabeformat transformiert.

---

## Zwischendaten (datasets/)

Der Ordner `datasets/` enthält alle von den Vorverarbeitungsskripten erzeugten Zwischendaten. Sie dienen als Eingabe für oemof-pipe und werden nicht manuell bearbeitet. Jeder Unterordner entspricht einem Verarbeitungsschritt der Pipeline.

### datasets/areas/

Zusammengeführte Nutzflächen (m²) und Nutzeinheiten pro Gebäudetyp und Cluster, getrennt nach den drei Wärmeversorgungstopologien (`central`, `decentral`, `low_temp_central`). Die Daten entstehen durch Zusammenführung der Unternehmens- und Wohngebäude-CSVs aus `raw/cluster/`. Erzeugt von `get_total_area_and_units.py`.

### datasets/areas_forecast/

Prognostizierte Nutzflächen und Nutzeinheiten für die Zeithorizonte `statusquo`, `2035` und `2050`, basierend auf Bebauungsplan-Wachstumsfaktoren. Die Spalten enthalten je Zeithorizont die erwartete Nutzfläche in m² und die Anzahl der Nutzeinheiten. Diese Daten sind die Grundlage für die NPRO-Szenariengestaltung. Erzeugt von `get_area_per_type_of_use_projection.py`.

### datasets/npro_buildings/

NPRO-Simulationsergebnisse, strukturiert in Unterordnern nach dem Schema `{year}_{climate}_{topology}/` (z. B. `2035_mean_rcp85_central/`). Jeder Unterordner enthält pro simuliertem Gebäudetyp:

- Eine **CSV-Datei** mit stündlichen Profilen (8760 Zeilen) für Strom (`plugLoadsProfile`, `emobProfile`), Wärme (`spaceHeatProfile`, `dhwProfile`), Kühlung (`spaceCoolProfile`, `processCoolProfile`) und weitere Größen.
- Eine **JSON-Datei** mit Gebäudemetadaten, darunter `buildingType` (residential/non-residential) und weitere NPRO-Konfigurationsparameter.

Die Unterordner werden durch `npro run all` befüllt, nachdem `get_demands_per_building.py` die Szenario-YAMLs erzeugt hat.

### datasets/demand_profiles/

Ausgabe von `get_demand_profiles.py`. Enthält zwei Arten von Dateien:

`total_demands.csv` aggregiert die Jahresenergiebedarfe aller Gebäude je Szenario im Langformat mit den Spalten `year_climate`, `name` und `amount`. Die Spalte `name` kodiert Energieträger, Topologie und Gebäudekategorie (z. B. `heat_central-residential-demand`). Diese Datei wird von oemof-pipe als skalare Bedarfsgröße eingelesen.

`{year}_{climate}.csv` (z. B. `2035_mean_rcp85.csv`) enthält normierte stündliche Profile im Bereich \[0, 1\] für alle Energieträger und Topologiekombinationen. Die Normierung erfolgt auf den jeweiligen Jahresgesamtbedarf. Spaltennamen folgen dem Schema `{energieträger}_{topologie}-{kategorie}`. Der Index ist ein Zeitstempel (`timeindex`).

### datasets/wind_profiles/

Normierte stündliche Windleistungszeitreihen, eine Datei pro TRY-Wetterdatei. Der Dateiname folgt dem Schema `wind_timeseries-{try_dateiname}-{year}.csv`. Jede Datei enthält eine einzige Spalte `wind_profile` mit Werten im Bereich \[0, 1\], normiert auf die Nennleistung der modellierten Windanlage. Erzeugt von `calc_wind_timeseries.py`.

---

## Datenpakete (datapackages/)

Der Ordner `datapackages/` enthält die fertigen oemof.tabular-Datenpakete, die von oemof-pipe aus Blueprint und Szenariodaten zusammengestellt werden. Die Struktur folgt dem [Frictionless Data Standard](https://frictionlessdata.io/).
Die Datenpakete werden erzeugt durch `oemof-pipe blueprint` (Templatedatei mit leeren Einträgen) und `oemof-pipe scenario` (Datenpaket pro Szenario):

- `datapackages/adlershof/` — Basisdatenpaket, erzeugt durch `oemof-pipe blueprint`. Enthält alle technologieunabhängigen Strukturen.
- `datapackages/adlershof_{SCENARIO}/` — Szenarienspezifisches Datenpaket, erzeugt durch `oemof-pipe scenario`. Enthält die für das Szenario angepassten Kapazitäten, Bedarfe und Zeitreihen.

### Verzeichnisstruktur

```
datapackages/{name}/
├── datapackage.json
└── data/
    ├── elements/
    │   ├── bus.csv
    │   ├── conversion.csv
    │   ├── volatile.csv
    │   ├── storages.csv
    │   ├── demands.csv
    │   ├── imports.csv
    │   ├── exports.csv
    │   ├── heatpumps.csv
    │   ├── flh_heatpumps.csv
    │   ├── backpressures.csv
    │   └── pth.csv
    └── sequences/
        ├── demands_profile.csv
        ├── volatile_profile.csv
        ├── heatpumps_profile.csv
        └── flh_heatpumps_profile.csv
```

### elements/

Jede CSV-Datei im Ordner `elements/` beschreibt einen oemof.tabular-Komponententyp. Jede Zeile entspricht einer Komponenteninstanz mit skalaren Parametern wie Kapazitäten, Wirkungsgraden und Kosten. Die genauen Spalten hängen vom Komponententyp ab und folgen der oemof.tabular-Konvention (z. B. `carrier`, `tech`, `capacity`, `efficiency`, `marginal_cost`).

### sequences/

Stündliche Zeitreihen als breite CSV-Dateien mit 8760 Datenzeilen (ein Jahr). Jede Spalte entspricht dem Profil einer Komponente; der Spaltenname folgt dem Schema `{komponentenname}-profile`. Die Sequenzen werden von oemof.tabular als Zeitreihenreferenz für die zugehörigen Elemente in `elements/` geladen.

### datapackage.json

Die Metadatendatei im Frictionless-Format listet alle Ressourcen (elements und sequences) mit Pfad, Feldschemata und Typ. oemof-tabular liest diese Datei beim Laden des Datenpaketes ein, um die Modellstruktur zu rekonstruieren.

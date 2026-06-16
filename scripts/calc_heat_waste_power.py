"""Calculate waste heat pump capacity potentials from energy profiles and COP time series."""

import pandas as pd

from settings import RAW_DIR, DATASETS_DIR
from utils.metadata import write_metadata

OUTPUT_DIR = DATASETS_DIR / "wasteheat_capacity"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "capacity.csv"

PERCENTILE = 95

WASTEHEAT_POTENTIAL_ENERGIES_FILE = (
    RAW_DIR / "wasteheat_potentials" / "Abwärmepotenziale_Adlershof.xlsx"
)
WASTEHEAT_POTENTIAL_ENERGIES = pd.read_excel(
    WASTEHEAT_POTENTIAL_ENERGIES_FILE
).set_index("(Ab-)Wärmequelle")

YEAR_INDEX_LOOKUP = {2025: 0, 2035: 1, 2050: 2}
POWER_LOOKUP = 7

TECH_MAPPING = {
    "BTB-Abwärmerückgewinnung (Hochtemperatur)": "heatpump_ht",
    "Chemie + Industrie + BTB (Mitteltemperatur)": "heatpump_mt",
    "Wäscherei, Büro und Labor": "heatpump_office",
    "Rechenzentrum + BTB (Niedertemperatur) + Industrie (Niedertemperatur)": "heatpump_nt",
    "Abwasser": "heatpump_wastewater",
    "Spree & Teltow-Kanal": "heatpump_canal",
    "Geothermie mitteltief": "heatpump_geothermal",
}
STATIC_HEATPUMPS = ("Abwasser", "Spree & Teltow-Kanal", "Geothermie mitteltief")


def get_energy(technology: str, year: int) -> float:
    year_column = YEAR_INDEX_LOOKUP[year]
    energy_total = float(WASTEHEAT_POTENTIAL_ENERGIES.loc[technology].iloc[year_column])
    energy_total *= 1000  # MWh -> kWh
    return energy_total


def get_power(technology: str) -> float:
    power = float(
        str(WASTEHEAT_POTENTIAL_ENERGIES.loc[technology].iloc[POWER_LOOKUP]).replace(
            ",", "."
        )
    )
    power *= 1000  # MW -> kW
    return power


def calculate_thermal_power(
    energy_series: pd.Series, cop: pd.Series, percentil: float
) -> float:
    if len(cop) != len(energy_series):
        print(
            f"Warning: File lengths differ! COP: {len(cop)}, Energy: {len(energy_series)}"
        )

    # Energy
    energy_total = energy_series.sum() / 1000

    # Power = Energy / COP
    power = energy_series / cop

    # Max peak power
    max_power = power.max() / 1000

    # get max peak power and calc percentile
    power_percentil = power.quantile(percentil / 100) / 1000

    # Full load hours
    energy_max = (power_percentil * cop).sum()

    # Thermal power
    power_thermal = power_percentil * cop.mean()

    print(f"Total Energy: {energy_total:.0f} MWh")
    print(f"Max Peak Power: {max_power:.2f} MW")
    print(f"{percentil}th Percentile: {power_percentil:.2f} MW")
    print(f"Energy max: {energy_max:.0f} MWh")
    print(f"Power thermal: {power_thermal:.2f} MW")
    print(f"Full load hours: {energy_total / power_thermal:.0f} h")
    print("------------")

    return power_thermal * 1000  # in kW


def get_dynamic_hp_powers(scenario: str, year: int) -> list[dict]:
    # Define paths
    cop_file = DATASETS_DIR / "wasteheat_cop" / f"cop_{year}.csv"
    energy_file = DATASETS_DIR / "wasteheat_profiles" / f"{scenario}.csv"

    # Read CSVs
    # cop.csv uses 'timeindex'
    # 2035_mean_rcp85.csv uses 'datetime'
    df_cop = pd.read_csv(cop_file, parse_dates=["timeindex"])
    df_energy = pd.read_csv(energy_file, parse_dates=["timeindex"])

    cop_columns = [column.removesuffix("-efficiency") for column in df_cop.columns]
    energy_columns = [
        column.removesuffix("-low_temperature_potential")
        for column in df_energy.columns
    ]
    technologies = set(cop_columns) & set(energy_columns)
    technologies.remove("timeindex")
    capacities = []
    for tech in technologies:
        print(tech)
        capacity = calculate_thermal_power(
            df_energy[f"{tech}-low_temperature_potential"],
            df_cop[f"{tech}-efficiency"],
            PERCENTILE,
        )
        capacities.append(
            {
                "scenario": scenario,
                "name": tech,
                "capacity_potential": round(capacity, 2),
            }
        )
    return capacities


def get_static_hp_data(scenario: str, year: int) -> list[dict]:
    data = []
    for raw_name, tech in TECH_MAPPING.items():
        if raw_name not in STATIC_HEATPUMPS:
            continue
        capacity = get_power(raw_name)
        full_load_hours = get_energy(raw_name, year) / capacity
        data.append(
            {
                "scenario": scenario,
                "name": tech,
                "capacity_potential": round(capacity, 2),
                "full_load_time_max": round(full_load_hours, 2),
            }
        )
    return data


if __name__ == "__main__":
    _scenario = "2035_mean_rcp85"
    _year = 2035
    dynamic_capacities = get_dynamic_hp_powers(_scenario, _year)
    static_capacities_and_flh = get_static_hp_data(_scenario, _year)
    df = pd.DataFrame(dynamic_capacities + static_capacities_and_flh)
    df.to_csv(OUTPUT_FILE, index=False)
    write_metadata(
        OUTPUT_DIR,
        script=__file__,
        description="Waste heat pump capacity potentials derived from waste heat energy profiles and COP time series.",
        inputs=[
            WASTEHEAT_POTENTIAL_ENERGIES_FILE,
            DATASETS_DIR / "wasteheat_cop" / f"cop_{_year}.csv",
            DATASETS_DIR / "wasteheat_profiles" / f"{_scenario}.csv",
        ],
        outputs=[OUTPUT_FILE],
        params={"scenario": _scenario, "year": _year, "percentile": PERCENTILE},
        sources=[],
    )

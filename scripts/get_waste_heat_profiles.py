"""Disaggregate annual waste heat potentials into hourly profiles by temperature level (HT/MT/NT/office)."""

import pandas as pd
import numpy as np
from settings import RAW_DIR, DATASETS_DIR
from utils.metadata import write_metadata

# =========================
# PATHS
# =========================
DEMANDS_DIR = DATASETS_DIR / "demand_profiles"

WASTEHEAT_POTENTIAL_FILE = (
    RAW_DIR / "wasteheat_potentials" / "Abwaermepotenzial_Adlershof_BfEE.csv"
)
WASTEHEAT_POTENTIAL = pd.read_csv(WASTEHEAT_POTENTIAL_FILE, sep=",")


# =========================
# TEMPERATURE CLASSIFICATION
# =========================
def classify_temp(temp_range):
    if temp_range in [">=110 °C", "90 - 110 °C"]:
        return "HT"
    elif temp_range in ["60 - 90 °C"]:
        return "MT"
    else:
        return "NT"


WASTEHEAT_POTENTIAL["Temp_Level"] = WASTEHEAT_POTENTIAL["Temperaturbereich"].apply(
    classify_temp
)

WASTEHEAT_POTENTIAL_ENERGIES_FILE = (
    RAW_DIR / "wasteheat_potentials" / "Abwärmepotenziale_Adlershof.xlsx"
)
WASTEHEAT_POTENTIAL_ENERGIES = pd.read_excel(
    WASTEHEAT_POTENTIAL_ENERGIES_FILE
).set_index("(Ab-)Wärmequelle")
OUTPUT_DIR = DATASETS_DIR / "wasteheat_profiles"
OUTPUT_DIR.mkdir(exist_ok=True)

# Lookup column in WASTEHEAT_POTENTIAL_ENERGIES_FILE (first column is used as index)
YEAR_INDEX_LOOKUP = {2025: 0, 2035: 1, 2050: 2}


def get_energy(technology: str, year: int) -> float:
    year_column = YEAR_INDEX_LOOKUP[year]
    energy_total = float(WASTEHEAT_POTENTIAL_ENERGIES.loc[technology].iloc[year_column])
    energy_total *= 1000  # MWh -> kWh
    return energy_total


def create_wasteheat_profiles(scenario_name: str, year: int):
    # =========================
    # LOAD DATA
    # =========================
    demand_profiles = pd.read_csv(DEMANDS_DIR / f"{scenario_name}.csv")

    # =========================
    # TIME INDEX
    # =========================

    datetimeindex = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    df_time = pd.DataFrame(index=datetimeindex)

    df_time["month"] = df_time.index.month
    df_time["hour"] = df_time.index.hour
    df_time["weekday"] = df_time.index.weekday

    # =========================
    # CENTRAL PROFILES
    # =========================
    central_heat = (
        demand_profiles["heat_central-non_residential"].values
        + demand_profiles["heat_central-residential"].values
    )
    central_heat = central_heat / central_heat.sum()

    central_cool = (
        demand_profiles["cool-non_residential"].values
        + demand_profiles["cool-residential"].values
    )
    central_cool = central_cool / central_cool.sum()

    # =========================
    # MONTHS
    # =========================
    months = [
        "Leistungsprofil Januar (in kW)",
        "Leistungsprofil Februar (in kW)",
        "Leistungsprofil März (in kW)",
        "Leistungsprofil April (in kW)",
        "Leistungsprofil Mai (in kW)",
        "Leistungsprofil Juni (in kW)",
        "Leistungsprofil Juli (in kW)",
        "Leistungsprofil August (in kW)",
        "Leistungsprofil September (in kW)",
        "Leistungsprofil Oktober (in kW)",
        "Leistungsprofil November (in kW)",
        "Leistungsprofil Dezember (in kW)",
    ]

    # =========================
    # TIME WINDOWS
    # =========================
    time_windows = {
        "Kälteanlage-HUB-Kältezentrale": (0, 24),
        "NSHV": (0, 24),
        "zentrales Kühlsystem": (0, 24),
        "Luftkondensator": (0, 24),
        "Druckluft": (0, 24),
        "Abwasser": (0, 24),
        "Abwärme aus Gewerbekälteanlage": (0, 24),
        "iKWK Modul": (6, 17),
        "NEZ Modul": (7, 16),
        "Glasmodul": (8, 16),
        "KKM": (8, 16),
        "RLT": (8, 16),
        "KM": (7, 22),
        "Kälte BFS 360": (6, 18),
    }

    def get_time_window(name):
        for key in time_windows:
            if key in str(name):
                return time_windows[key]
        return (0, 24)

    # =========================
    # FUNCTIONS
    # =========================
    def get_monthly_weights(row):
        values = row[months].values.astype(float)
        if values.sum() == 0:
            return np.ones(12) / 12
        return values / values.sum()

    def availability_mask(row):
        start, end = get_time_window(row["Name des Abwärmepotentials"])

        mask = (df_time["hour"] >= start) & (df_time["hour"] < end)
        mask = mask.astype(float)

        hours_per_day = row["Durchschnittliche tägl. Verfügbarkeit (in h)"]
        window_length = max(end - start, 1)

        mask *= min(hours_per_day / window_length, 1)

        if row["Verfügbarkeit am Wochenende"] == "Nein":
            mask[df_time["weekday"] >= 5] = 0

        return mask.values

    def generate_profile(row):
        weights = get_monthly_weights(row)
        availability = availability_mask(row)

        total_energy = row["Wärmemenge pro Jahr (in kWh/a)"]
        profile = np.zeros(len(df_time))

        # 🔥 Auswahl Profilbasis
        if row["Temp_Level"] == "NT":
            base_profile_global = central_cool
        else:
            base_profile_global = central_heat

        for m in range(1, 13):
            month_mask = (df_time["month"] == m).values

            base = base_profile_global * availability * month_mask

            if base.sum() == 0:
                base = base_profile_global * month_mask

            if base.sum() == 0:
                base = month_mask.astype(float)

            base = base / base.sum()
            monthly_energy = weights[m - 1] * total_energy

            profile += base * monthly_energy

        return profile

    # =========================
    # GENERATE PROFILES
    # =========================
    profiles = []

    for _, row in WASTEHEAT_POTENTIAL.iterrows():
        profiles.append(generate_profile(row))

    WASTEHEAT_POTENTIAL["profile"] = profiles

    # =========================
    # AGGREGATION
    # =========================
    def aggregate_profiles(df, level):
        subset = df[df["Temp_Level"] == level]

        if len(subset) == 0:
            return np.zeros(len(df_time)), 0

        profile = np.sum(subset["profile"].tolist(), axis=0)
        energy_sum = subset["Wärmemenge pro Jahr (in kWh/a)"].sum()

        return profile, energy_sum

    ht_profile, ht_energy = aggregate_profiles(WASTEHEAT_POTENTIAL, "HT")
    mt_profile, mt_energy = aggregate_profiles(WASTEHEAT_POTENTIAL, "MT")
    nt_profile, nt_energy = aggregate_profiles(WASTEHEAT_POTENTIAL, "NT")

    # Apply energy for given year
    ht_profile = (
        ht_profile
        / ht_profile.sum()
        * get_energy("BTB-Abwärmerückgewinnung (Hochtemperatur)", year)
    )
    mt_profile = (
        mt_profile
        / mt_profile.sum()
        * get_energy("Chemie + Industrie + BTB (Mitteltemperatur)", year)
    )
    nt_profile = (
        nt_profile
        / nt_profile.sum()
        * get_energy(
            "Rechenzentrum + BTB (Niedertemperatur) + Industrie (Niedertemperatur)",
            year,
        )
    )

    # Add profile for
    office_energy = get_energy("Wäscherei, Büro und Labor", year)
    office_profile = central_cool * office_energy

    def log_profile_sum(name, profile):
        print(f"{name}: {profile.sum() / 1000:.2f} MWh")

    log_profile_sum("HT", ht_profile)
    log_profile_sum("MT", mt_profile)
    log_profile_sum("NT", nt_profile)
    log_profile_sum("office", office_profile)

    # =========================
    # SAVE
    # =========================
    df = pd.DataFrame(
        {
            "timeindex": df_time.index,
            "heatpump_ht-low_temperature_potential": ht_profile,
            "heatpump_mt-low_temperature_potential": mt_profile,
            "heatpump_nt-low_temperature_potential": nt_profile,
            "heatpump_office-low_temperature_potential": office_profile,
        }
    )
    output_file = OUTPUT_DIR / f"{scenario_name}.csv"
    df.to_csv(output_file, index=False)
    write_metadata(
        OUTPUT_DIR,
        script=__file__,
        description="Hourly waste heat potential profiles per temperature level (HT/MT/NT/office), disaggregated from annual energy totals using demand-driven temporal patterns.",
        inputs=[
            WASTEHEAT_POTENTIAL_FILE,
            WASTEHEAT_POTENTIAL_ENERGIES_FILE,
            DEMANDS_DIR / f"{scenario_name}.csv",
        ],
        outputs=[output_file],
        params={"scenario": scenario_name, "year": year},
    )


if __name__ == "__main__":
    import sys

    _scenario = sys.argv[1] if len(sys.argv) > 1 else "2035_mean_rcp85"
    _year = int(sys.argv[2]) if len(sys.argv) > 2 else 2035
    create_wasteheat_profiles(_scenario, _year)

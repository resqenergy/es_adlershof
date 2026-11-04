"""Calculate capacities and the max profile of the LT <-> HT heat exchangers from demand profiles."""

import pandas as pd
import sys

from settings import DATASETS_DIR
from utils.metadata import write_metadata

CAPACITY_DIR = DATASETS_DIR / "heat_exchanger_capacity"
MAX_PROFILE_DIR = DATASETS_DIR / "heat_exchanger_max_profiles"
CAPACITY_DIR.mkdir(exist_ok=True)
MAX_PROFILE_DIR.mkdir(exist_ok=True)

DEMAND_PROFILES_DIR = DATASETS_DIR / "demand_profiles"

T_SUP_HT = 110
T_RET_HT = 55
DELTA_T_RL_PERM = 10

HT_CARRIERS = ("heat_central-residential", "heat_central-non_residential")
LT_CARRIER = "heat_lt_central-residential"

HT_TO_LT = "heat_central-heat_exchanger"
LT_TO_HT = "heat_lt_central-heat_exchanger"
MAX_PROFILE_COLUMN = f"{LT_TO_HT}-max"


def get_alpha() -> float:
    """Share of the HT peak that can be fed back into the HT return line."""
    return DELTA_T_RL_PERM / (T_SUP_HT - T_RET_HT)


def get_annual_demand_mwh(
    demand_totals: pd.DataFrame, scenario: str, carrier: str
) -> float:
    rows = demand_totals[
        (demand_totals["year_climate"] == scenario)
        & (demand_totals["name"] == f"{carrier}-demand")
    ]
    if rows.empty:
        raise ValueError(f"No annual demand for '{carrier}' in scenario '{scenario}'.")
    return float(rows["amount"].iloc[0])


def get_load_mw(
    demand_profiles: pd.DataFrame,
    demand_totals: pd.DataFrame,
    scenario: str,
    carriers: tuple[str, ...],
) -> pd.Series:
    """Hourly load in MW: normalized profile (sum 1) times annual demand in MWh."""
    load = pd.Series(0.0, index=demand_profiles.index)
    for carrier in carriers:
        annual_mwh = get_annual_demand_mwh(demand_totals, scenario, carrier)
        load += demand_profiles[carrier] * annual_mwh
    return load


def calc_capacities(ht_load: pd.Series, lt_load: pd.Series) -> dict[str, float]:
    """Nominal capacities in MW for both heat exchanger directions."""
    print(f"HT peak: {ht_load.max():.2f} MW")
    print(f"LT peak: {lt_load.max():.2f} MW")
    print(f"alpha: {get_alpha():.3f}")
    print("------------")
    return {
        HT_TO_LT: lt_load.max(),
        LT_TO_HT: get_alpha() * ht_load.max(),
    }


def calc_max_profile(ht_load: pd.Series) -> pd.Series:
    """Feed-in limit LT -> HT as share of the HT peak (max = 1 at peak hour)."""
    return ht_load / ht_load.max()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        raise ValueError("Scenario must be set.")
    _scenario = sys.argv[1]

    _profiles = pd.read_csv(DEMAND_PROFILES_DIR / f"{_scenario}.csv")
    _totals = pd.read_csv(DEMAND_PROFILES_DIR / "total_demands.csv")
    _ht_load = get_load_mw(_profiles, _totals, _scenario, HT_CARRIERS)
    _lt_load = get_load_mw(_profiles, _totals, _scenario, (LT_CARRIER,))

    _capacities = calc_capacities(_ht_load, _lt_load)
    capacity_file = CAPACITY_DIR / f"capacity_{_scenario}.csv"
    pd.DataFrame(
        [
            {"scenario": _scenario, "name": name, "capacity": capacity}
            for name, capacity in _capacities.items()
        ]
    ).to_csv(capacity_file, index=False)

    max_file = MAX_PROFILE_DIR / f"max_{_scenario}.csv"
    pd.DataFrame(
        {
            "timeindex": _profiles["timeindex"],
            MAX_PROFILE_COLUMN: calc_max_profile(_ht_load),
        }
    ).to_csv(max_file, index=False)

    _params = {
        "scenario": _scenario,
        "T_SUP_HT": T_SUP_HT,
        "T_RET_HT": T_RET_HT,
        "delta_T_RL_perm": DELTA_T_RL_PERM,
        "alpha": get_alpha(),
    }
    _inputs = [
        DEMAND_PROFILES_DIR / f"{_scenario}.csv",
        DEMAND_PROFILES_DIR / "total_demands.csv",
    ]
    write_metadata(
        CAPACITY_DIR,
        script=__file__,
        description="Nominal capacities (MW) of the LT <-> HT heat exchangers, derived from heat demand profiles and annual demands.",
        inputs=_inputs,
        outputs=[capacity_file],
        params=_params,
        sources=[],
        filename=f"{capacity_file.stem}.metadata.json",
    )
    # Written last: the Makefile uses this metadata file as completion marker.
    write_metadata(
        MAX_PROFILE_DIR,
        script=__file__,
        description="Hourly feed-in limit (share of HT peak) for the LT -> HT heat exchanger, derived from the HT heat demand profile.",
        inputs=_inputs,
        outputs=[max_file],
        params=_params,
        sources=[],
        filename=f"{max_file.stem}.metadata.json",
    )

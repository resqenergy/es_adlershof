"""Tests for deriving LT <-> HT heat exchanger capacities and max profile."""

import pandas as pd
import pytest

from scripts import calc_heat_exchanger as che


@pytest.fixture
def demand_totals():
    return pd.DataFrame(
        [
            ("s1", "heat_central-residential-demand", 10.0),
            ("s1", "heat_central-non_residential-demand", 30.0),
            ("s1", "heat_lt_central-residential-demand", 4.0),
        ],
        columns=["year_climate", "name", "amount"],
    )


@pytest.fixture
def demand_profiles():
    # normalized profiles: each column sums to 1
    return pd.DataFrame(
        {
            "heat_central-residential": [0.25, 0.25, 0.5, 0.0],
            "heat_central-non_residential": [0.0, 0.5, 0.5, 0.0],
            "heat_lt_central-residential": [0.5, 0.0, 0.0, 0.5],
        },
        index=pd.date_range("2050-01-01", periods=4, freq="h"),
    )


def test_alpha_from_temperatures(monkeypatch):
    monkeypatch.setattr(che, "T_SUP_HT", 90)
    monkeypatch.setattr(che, "T_RET_HT", 50)
    monkeypatch.setattr(che, "DELTA_T_RL_PERM", 4)
    assert che.get_alpha() == pytest.approx(0.1)


def test_load_mw_is_profile_times_annual_demand(demand_profiles, demand_totals):
    ht_load = che.get_load_mw(
        demand_profiles, demand_totals, "s1", che.HT_CARRIERS
    )
    # residential: 10 MWh * profile, non_residential: 30 MWh * profile
    expected = pd.Series([2.5, 2.5 + 15.0, 5.0 + 15.0, 0.0], index=ht_load.index)
    pd.testing.assert_series_equal(ht_load, expected, check_names=False)
    # hourly MW summed over the year gives the annual demand in MWh
    assert ht_load.sum() == pytest.approx(40.0)


def test_lt_load_uses_only_lt_carrier(demand_profiles, demand_totals):
    lt_load = che.get_load_mw(
        demand_profiles, demand_totals, "s1", (che.LT_CARRIER,)
    )
    assert lt_load.sum() == pytest.approx(4.0)


def test_missing_scenario_raises(demand_profiles, demand_totals):
    with pytest.raises(ValueError, match="No annual demand"):
        che.get_load_mw(demand_profiles, demand_totals, "other", che.HT_CARRIERS)


def test_capacities_and_max_profile(monkeypatch):
    monkeypatch.setattr(che, "T_SUP_HT", 90)
    monkeypatch.setattr(che, "T_RET_HT", 50)
    monkeypatch.setattr(che, "DELTA_T_RL_PERM", 4)
    ht_load = pd.Series([2.0, 8.0, 4.0])
    lt_load = pd.Series([1.0, 3.0, 2.0])

    capacities = che.calc_capacities(ht_load, lt_load)

    assert capacities[che.HT_TO_LT] == pytest.approx(3.0)  # LT peak
    assert capacities[che.LT_TO_HT] == pytest.approx(0.1 * 8.0)  # alpha * HT peak
    max_profile = che.calc_max_profile(ht_load)
    assert list(max_profile) == pytest.approx([0.25, 1.0, 0.5])
    assert max_profile.max() == pytest.approx(1.0)

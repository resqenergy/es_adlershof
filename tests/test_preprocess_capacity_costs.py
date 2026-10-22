"""Tests for annualizing overnight capacity costs."""

import pandas as pd
import pytest

from scripts.preprocess_capacity_costs import calculate_annual_cost


def test_capacity_cost_is_annuity_plus_fixom_per_component_lifetime(tmp_path):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    pd.DataFrame(
        [
            ("s1", "boiler", "lifetime", 20),
            ("s1", "boiler", "capacity_cost_overnight", 1000),
            ("s1", "boiler", "fixom_cost", 20),
            ("s1", "battery", "lifetime", 10),
            ("s1", "battery", "capacity_cost_overnight", 500),
            ("s1", "battery", "fixom_cost", 10),
            ("s1", "battery", "storage_capacity_cost_overnight", 200),
            ("s1", "battery", "storage_fixom_cost", 5),
        ],
        columns=["scenario_key", "name", "var_name", "var_value"],
    ).to_csv(input_file, sep=";", index=False)

    calculate_annual_cost(input_file, output_file)

    result = pd.read_csv(output_file, sep=";").set_index("name")
    # annuity = capex * wacc * (1 + wacc)^n / ((1 + wacc)^n - 1), wacc = 0.04
    # boiler:  1000 * 0.073582 + 20 = 93.5818
    assert result.loc["boiler", "capacity_cost"] == pytest.approx(93.5818, abs=1e-4)
    # battery: 500 * 0.123291 + 10 = 71.6455
    assert result.loc["battery", "capacity_cost"] == pytest.approx(71.6455, abs=1e-4)
    # battery: 200 * 0.123291 + 5 = 29.6582
    assert result.loc["battery", "storage_capacity_cost"] == pytest.approx(
        29.6582, abs=1e-4
    )

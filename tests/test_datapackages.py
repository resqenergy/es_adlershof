"""Consistency checks on built scenario datapackages."""

import pandas as pd
import pytest

from settings import ROOT_DIR

DATAPACKAGES_DIR = ROOT_DIR / "datapackages"
SCENARIOS_DIR = ROOT_DIR / "scenarios"


def scenario_datapackages():
    """Return built datapackages that belong to a scenario (blueprints are skipped)."""
    return [
        path
        for path in sorted(DATAPACKAGES_DIR.glob("adlershof_*"))
        if (SCENARIOS_DIR / f"{path.name.removeprefix('adlershof_')}.yaml").exists()
    ]


def test_expandable_components_have_capacity_cost():
    datapackages = scenario_datapackages()
    if not datapackages:
        pytest.skip("No scenario datapackage found, run `make datapackage` first.")

    missing = []
    for datapackage in datapackages:
        for elements_file in sorted((datapackage / "data" / "elements").glob("*.csv")):
            df = pd.read_csv(elements_file, sep=";")
            if "expandable" not in df:
                continue
            expandable = df[df["expandable"].astype(str).str.lower() == "true"]
            cost_columns = [c for c in df.columns if c.endswith("capacity_cost")]
            for column in cost_columns:
                for name in expandable.loc[expandable[column].isna(), "name"]:
                    missing.append(
                        f"{datapackage.name}/{elements_file.name}: {name} has no {column}"
                    )

    assert not missing, "Expandable components without capacity cost:\n" + "\n".join(
        missing
    )

def test_expandable_components_have_capacity():
    datapackages = scenario_datapackages()
    if not datapackages:
        pytest.skip("No scenario datapackage found, run `make datapackage` first.")

    missing = []
    for datapackage in datapackages:
        for elements_file in sorted((datapackage / "data" / "elements").glob("*.csv")):
            df = pd.read_csv(elements_file, sep=";")
            if "expandable" not in df:
                continue
            expandable = df[df["expandable"].astype(str).str.lower() == "true"]
            capacity_columns = [c for c in df.columns if c.endswith("capacity")]
            for column in capacity_columns:
                for name in expandable.loc[expandable[column].isna(), "name"]:
                    missing.append(
                        f"{datapackage.name}/{elements_file.name}: {name} has no {column}"
                    )

    assert not missing, "Expandable components without capacity:\n" + "\n".join(
        missing
    )
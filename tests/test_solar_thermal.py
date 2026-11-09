"""Checks that the LT central solar thermal profile is wired as a dispatchable sequence.

The profile is an upper bound (dispatchable), not a forced output (volatile).
The scenario check reads YAML only; the datapackage check needs a built
datapackage and is skipped otherwise.
"""

import pandas as pd
import pytest
import yaml

from settings import ROOT_DIR

SCENARIOS_DIR = ROOT_DIR / "scenarios"
DATAPACKAGES_DIR = ROOT_DIR / "datapackages"

LT_NAME = "heat_lt_central-solarthermal"
LT_PROFILE = f"{LT_NAME}-profile"

# legacy.yaml predates the current blueprint (uses solar_profile, no LT solar thermal)
LEGACY_SCENARIOS = {"legacy"}


def _scenario_files():
    return sorted(
        path for path in SCENARIOS_DIR.glob("*.yaml") if path.stem not in LEGACY_SCENARIOS
    )


@pytest.mark.parametrize("scenario", _scenario_files(), ids=lambda p: p.stem)
def test_scenario_maps_lt_profile_to_dispatchable_sequence(scenario):
    with scenario.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)
    mappings = [
        entry
        for entry in config.get("sequences", [])
        if LT_PROFILE in (entry.get("column_mapping") or {}).values()
    ]
    assert mappings, f"{scenario.name}: no sequence provides {LT_PROFILE}"
    for entry in mappings:
        assert entry["sequence_name"] == "dispatchable_profile", (
            f"{scenario.name}: {LT_PROFILE} is mapped to "
            f"'{entry['sequence_name']}', expected 'dispatchable_profile'"
        )


def _built_scenario_datapackages():
    return [
        path
        for path in sorted(DATAPACKAGES_DIR.glob("adlershof_*"))
        if (SCENARIOS_DIR / f"{path.name.removeprefix('adlershof_')}.yaml").exists()
    ]


@pytest.mark.parametrize(
    "datapackage", _built_scenario_datapackages(), ids=lambda p: p.name
)
def test_built_lt_solarthermal_profile_is_a_valid_upper_bound(datapackage):
    sequences = datapackage / "data" / "sequences"
    profile_file = sequences / "dispatchable_profile.csv"
    if not profile_file.exists():
        pytest.skip(f"{profile_file.name} missing, run `make datapackage` first.")

    profiles = pd.read_csv(profile_file, sep=";", index_col="timeindex")
    assert LT_PROFILE in profiles.columns
    series = profiles[LT_PROFILE]
    # profile is an upper bound per unit capacity: non-negative, at most ~1
    assert series.min() >= 0
    assert series.max() <= 1.0
    assert series.sum() > 0, "LT solar thermal profile is all zero"

    # the volatile sequence must not carry the LT profile anymore
    volatile_file = sequences / "volatile_profile.csv"
    if volatile_file.exists():
        volatile_columns = pd.read_csv(volatile_file, sep=";", nrows=0).columns
        assert LT_PROFILE not in volatile_columns

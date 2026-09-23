# ADR 0001: Makefile targets skip existing outputs

- Status: accepted
- Date: 2026-09-23

## Context

All Makefile targets were `.PHONY`, so every `make all` recomputed the whole
pipeline, including the slow NPRO simulation (remote API) and GSEE. Some
datasets are produced once per scenario/year (`SCENARIO`, `YEAR` make
variables) and partly overwrote each other (`wasteheat_capacity/capacity.csv`,
the shared `metadata.json` in the wasteheat folders, `datapackages/adlershof/`
built with a year-dependent time index).

## Decision

1. **Completion marker = metadata file.** Every script writes its
   `metadata.json` (via `utils.metadata.write_metadata`) as the last step. Make
   uses that file as the target, so a crashed run leaves no marker and is
   repeated. `calc_gsee_timeseries` and `calc_pv_timeseries` now write metadata
   too.
2. **All-at-once scripts stay as they are.** Scripts that loop over all
   scenarios internally (areas, npro, demand profiles, solar thermal, gsee, pv,
   bev, wind, parameters) keep their flat folders; target is
   `datasets/<dataset>/metadata.json`.
3. **Per-scenario/year outputs: key in the file name, no extra folder layer.**
   Wasteheat datasets stay flat. Scenario or year is part of the file name and
   each output file gets its own metadata file (`write_metadata(...,
   filename=...)`):
   - `wasteheat_profiles/{SCENARIO}.csv` + `{SCENARIO}.metadata.json`
   - `wasteheat_cop/cop_{YEAR}.csv` + `cop_{YEAR}.metadata.json`
   - `wasteheat_capacity/capacity_{SCENARIO}.csv` + `capacity_{SCENARIO}.metadata.json`
     (was `capacity.csv`)

   A folder layer per scenario/year (`<dataset>/<key>/`) was considered and
   rejected: it only affected three datasets and added path depth without
   benefit.
4. **Rebuild semantics.** Metadata targets use normal prerequisites: if an
   upstream dataset is rebuilt, downstream datasets are rebuilt. Changes to
   scripts, `raw/` or `config/` are not tracked (too much upkeep, rebuilds on
   docstring edits); force with `make -B <target>` or by deleting the output.
5. **Folder targets are existence-only.** `datasets/npro_buildings/` (external
   `npro run all`, no metadata), `datapackages/adlershof_{YEAR}/` (blueprint)
   and `datapackages/adlershof_{SCENARIO}/` (scenario) use order-only
   prerequisites. Directory mtimes are unreliable, and NPRO must never run by
   accident. The blueprint is keyed by `YEAR` because its time index depends on
   it.
6. `oemof-pipe -f` checks the blueprint/scenario name instead of `--target`, so
   the datapackage recipes `rm -rf` their target before building.
7. `YEAR` and `SCENARIO` remain independent make variables.
8. The previous phony target names remain as aliases; `export_datapackage` and
   `docs` stay phony.

## Consequences

- `make all` only computes what is missing.
- A partially failed `npro run all` leaves `datasets/npro_buildings/` behind and
  is not retried automatically; delete the folder to rerun.
- Existing local data needs a one-time cleanup: delete `datasets/wasteheat_*`
  and `datapackages/adlershof_2050/` (possibly stale from an old run).

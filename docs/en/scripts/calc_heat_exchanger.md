# Heat exchangers LT ↔ HT

## Purpose

Computes the nominal capacities of the two heat exchangers between the high-temperature (HT) and low-temperature (LT) networks for each scenario, as well as the hourly feed-in limit of the LT → HT heat exchanger (max profile). The results enter oemof-pipe via the scenario files.

## Background: why the LT → HT heat exchanger is limited

The LT network is hydraulically separated from the HT network. It is supplied from the HT return line via a heat exchanger (direction HT → LT). In the opposite direction, heat from the LT network, for example a solar thermal surplus, can be fed into the HT return line (direction LT → HT). This direction is limited.

**Reason:** Feed-in raises the HT return temperature. The rise is capped at ΔT_RL,perm, because otherwise the generators on the HT network lose efficiency and grid losses increase. (Background and discussion: [PR #20](https://github.com/resqenergy/es_adlershof/pull/20).)

**Derivation:** For the heat flow in the HT network at any point in time

$$Q_\text{HT} = \dot{m} \cdot c_p \cdot (T_\text{SUP,HT} - T_\text{RET,HT})$$

The fed-in heat $Q_\text{LT→HT}$ raises the return temperature by

$$\Delta T = \frac{Q_\text{LT→HT}}{\dot{m} \cdot c_p}$$

Setting $\Delta T = \Delta T_\text{RL,perm}$ gives the maximum feed-in

$$Q_\text{LT→HT} \le \alpha \cdot Q_\text{HT} \qquad \text{with} \qquad \alpha = \frac{\Delta T_\text{RL,perm}}{T_\text{SUP,HT} - T_\text{RET,HT}}$$

**Consequences:**

- The limit depends on the HT load at each point in time. It is therefore time-dependent, not constant.
- The nominal capacity of the heat exchanger is $\alpha$ times the HT peak load. The max profile describes the time course as the share of the HT load relative to its peak.
- Since $T_\text{SUP,HT} > T_\text{RET,HT}$, $\alpha$ is below 1.
- Simplifications: grid losses and the effect of return-line loading on generator efficiencies are not modeled.

## Inputs

| File | Description |
|------|-------------|
| `datasets/demand_profiles/{scenario}.csv` | Normalized hourly demand profiles per carrier (sum per carrier = 1), column `timeindex` |
| `datasets/demand_profiles/total_demands.csv` | Annual demands per scenario and carrier in MWh (columns `year_climate`, `name`, `amount`) |

Carriers used:

- **HT load:** `heat_central-residential` and `heat_central-non_residential`
- **LT load:** `heat_lt_central-residential`

## Outputs

**Capacities:** `datasets/heat_exchanger_capacity/capacity_{scenario}.csv` (metadata: `capacity_{scenario}.metadata.json`)

| Column | Description |
|--------|-------------|
| `scenario` | Scenario name |
| `name` | `heat_central-heat_exchanger` (HT → LT) or `heat_lt_central-heat_exchanger` (LT → HT) |
| `capacity` | Nominal capacity in MW |

| `name` | Nominal capacity |
|--------|-------------|
| `heat_central-heat_exchanger` | Peak of the LT load |
| `heat_lt_central-heat_exchanger` | $\alpha \cdot$ HT peak |

**Max profile:** `datasets/heat_exchanger_max_profiles/max_{scenario}.csv` (metadata: `max_{scenario}.metadata.json`)

| Column | Description |
|--------|-------------|
| `timeindex` | Hourly timestamp |
| `heat_lt_central-heat_exchanger-max` | HT load in the hour divided by the HT peak (value between 0 and 1, maximum = 1) |


## Parameters

| Parameter | Value | Description |
|-----------|------|-------------|
| `T_SUP_HT` | 110 °C | Supply temperature of the HT network (preliminary assumption) |
| `T_RET_HT` | 55 °C | Return temperature of the HT network (preliminary assumption) |
| `DELTA_T_RL_PERM` | 10 K | Permissible rise of the HT return temperature due to feed-in (preliminary assumption) |
| `alpha` | ≈ 0.18 | Calculated from the three values above: 10 / (110 − 55) |

The temperatures are assumptions that must be validated within the project consortium.

The efficiencies of the heat exchangers (0.99 for HT → LT, 0.98 for LT → HT) are not set in this script. They are passed as parameters from outside the script.

## Algorithm

1. **Compute loads** — For each carrier, the hourly load in MW is formed: normalized profile × annual demand in MWh. The sum over the carriers gives the HT load and the LT load.
2. **Determine nominal capacities** — HT → LT: peak of the LT load. LT → HT: $\alpha$ × peak of the HT load.
3. **Build max profile** — HT load per hour divided by its peak.
4. **Save** — Capacities and max profile as CSV, each with a metadata file.

## Execution

```bash
make heat_exchangers SCENARIO=2035_mean_rcp85
```

Alternatively, directly:

```bash
uv run -m scripts.calc_heat_exchanger 2035_mean_rcp85
```

The tests are located in `tests/test_calc_heat_exchanger.py`.

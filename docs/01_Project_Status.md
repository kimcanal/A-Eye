# Project Status: A-Eye

## Current Active Scope

The current repository is centered on **one active implementation path**:

- `Yeoksam-dong 3x3 micro area`
- `5-minute synthetic taxi demand`
- `rule-based dispatch`
- `before / after SUMO export`
- `visual comparison board + motion playback`

Everything else should be treated as archived or secondary.

## Assignment Requirements Mapping

| Module | Requirement | Current Status | Current Active Interpretation |
| :--- | :--- | :--- | :--- |
| **Module 1** | Digital Twin / Simulation | **Partially satisfied** | SUMO-based digital twin exists for a simplified 3x3 Yeoksam network. |
| **Module 2** | Data Pipeline & Features | **Partially satisfied** | Synthetic 5-minute zone demand is generated and converted into dispatch inputs. |
| **Module 3** | Prediction | **Not the active path yet** | The current Yeoksam baseline skips ML on purpose to stabilize the simulation path first. |
| **Module 4** | Dispatch | **Satisfied for baseline demo** | Rule-based reallocation works and produces measurable before/after differences. |

## What Is Working Right Now

- A Yeoksam 3x3 demand table is generated at 5-minute intervals.
- Dispatch recommendations are produced from the latest demand state.
- `before` and `after` SUMO route/config files are exported.
- SUMO CLI accepts the generated config files.
- The repository also produces:
  - a before/after summary board
  - a motion playback GIF derived from SUMO routes

## What Is Not in the Active Path

These exist only as legacy or secondary work now:

- Unity-based visual experiments
- Seoul public-data hourly pipeline
- ConvLSTM / public-data experimental branch
- older public-data SUMO route generation

## Next Practical Step

The next meaningful milestone is:

- keep the current SUMO baseline stable
- optionally add a simple ML baseline on top of the same Yeoksam 5-minute structure

That is a much better next step than expanding the repository back into multiple competing paths.

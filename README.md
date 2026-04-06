# A-Eye

Kakao Mobility capstone repository for a **Yeoksam-dong 3x3 taxi dispatch Digital Twin**.

The repo currently has one active path:
- **SUMO baseline**
- **5-minute synthetic Yeoksam demand**
- **rule-based dispatch**
- **before / after comparison**

Everything else should be treated as reference or legacy work.

## Current Focus

We are using a small Yeoksam 3x3 micro-area to validate the assignment flow:

1. generate 5-minute demand
2. build dispatch inputs
3. compare `before` vs `after`
4. export both cases to SUMO

Main entry point:

```bash
bash scripts/run_yeoksam_sumo_pipeline.sh
```

Main outputs:
- `outputs/yeoksam_sumo/dispatch_recommendations.csv`
- `outputs/yeoksam_sumo/dispatch_comparison.csv`
- `outputs/yeoksam_sumo/dispatch_evaluation.json`
- `module1_sumo/yeoksam_before.sumocfg`
- `module1_sumo/yeoksam_after.sumocfg`

## What To Read First

- [docs/README.md](docs/README.md)
- [docs/01_Project_Status.md](docs/01_Project_Status.md)
- [docs/03_SUMO_Simulation.md](docs/03_SUMO_Simulation.md)
- [docs/22_Yeoksam_SUMO_Baseline.md](docs/22_Yeoksam_SUMO_Baseline.md)

## Top-Level Guide

- `configs/`
  - active YAML configs
- `src/`
  - active Python pipeline code
- `scripts/`
  - runnable entry scripts
- `module1_sumo/`
  - SUMO network, route, and config files
- `docs/`
  - active docs plus archived notes
- `data/`
  - local/generated datasets
- `outputs/`
  - generated results

## Legacy / Secondary Paths

These are kept, but they are not the main path right now:
- `legacy/unity/`
- `legacy/module1_simulation/`
- public hourly Seoul-data experiments
- older planning and meeting notes under `docs/archive/`

## Cleanup

If generated files get noisy:

```bash
bash scripts/clean_generated_outputs.sh safe
bash scripts/clean_generated_outputs.sh intermediate
bash scripts/clean_generated_outputs.sh all
```

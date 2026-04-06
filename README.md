# A-Eye: Taxi Demand Prediction & Dispatch Simulation

A-Eye is a taxi demand forecasting and dispatch simulation project for the **Kakao Mobility Capstone**.

## Current Scope

- **Baseline demand prediction**: Seoul public transit demand is fetched, transformed, and used to train a stable RandomForest baseline.
- **Experimental deep learning path**: A custom ConvLSTM runs on a synthetic 3x3 hotspot grid for spatio-temporal experiments.
- **Dispatch ranking**: Dispatch recommendations are currently generated from the refreshed baseline prediction output.
- **Simulation bridge**: SUMO route files are generated from ConvLSTM output as a coarse simulation demo.
- **Assignment-aligned fallback path**: a Yeoksam-dong 3x3 synthetic 5-minute SUMO baseline now exists for fast Digital Twin validation before ML.

## Important Notes

- Public weather and holiday features are enabled, but **weather is still mock-generated** inside the preprocessing step.
- The SUMO export currently demonstrates pipeline connectivity, not fully realistic spatial routing.
- Older planning and draft documents were moved under `docs/archive/` to keep the active docs slimmer.

## Project Structure

- `src/`: Core Python modules for data, preprocessing, prediction, dispatch, analysis, and visualization.
- `docs/`: Active project docs.
- `docs/archive/`: Older notes and archived drafts.
- `module1_sumo/`: SUMO network/config/route files.
- `module1_simulation/`: Unity/minimal simulation assets and logic.
- `configs/`: YAML configuration for local and public-data runs.
- `scripts/`: End-to-end execution scripts and utility scripts.

## Quick Start

### 1. Configure the environment

```bash
export SEOUL_OPEN_API_KEY="your_api_key_here"
```

### 2. Run the public-data pipeline

This fetches Seoul public data, builds features, refreshes the baseline prediction used by dispatch, and regenerates the presentation-facing analysis outputs.

```bash
bash scripts/run_public_pipeline.sh
```

### 3. Optional: Run the experimental ConvLSTM/SUMO branch

This is now separated from the default public pipeline so the visible baseline/dispatch path stays lighter.

```bash
bash scripts/run_public_experiments.sh
```

After the run, the public-data folder also includes a readable zone lookup:

- `data/seoul_public/zone_lookup.csv`

This maps each `zone_id` to `zone_name`, `gu_name`, and `full_zone_name` so that downstream CSV outputs are easier to read.

### 4. Optional: Launch SUMO

```bash
cd module1_sumo
sumo-gui -c sumo_config.sumocfg
```

### 5. Run the Yeoksam 3x3 SUMO baseline

This is the easiest current path if we want to stay close to the assignment scope and defer ML for now.

```bash
bash scripts/run_yeoksam_sumo_pipeline.sh
```

Key outputs:
- `data/yeoksam_synthetic_5min.csv`
- `outputs/yeoksam_sumo/dispatch_recommendations.csv`
- `outputs/yeoksam_sumo/dispatch_evaluation.json`
- `module1_sumo/yeoksam_before.sumocfg`
- `module1_sumo/yeoksam_after.sumocfg`

### 6. Optional: Clean generated files

If the generated CSV/PNG/JSON files feel too noisy during development:

```bash
bash scripts/clean_generated_outputs.sh safe
bash scripts/clean_generated_outputs.sh intermediate
bash scripts/clean_generated_outputs.sh all
```

## Output Layout

- `outputs/local/`: local synthetic pipeline outputs
- `outputs/seoul_public/`: Seoul public-data baseline/dispatch outputs
- `outputs/yeoksam_sumo/`: Yeoksam 3x3 synthetic SUMO baseline outputs
- `outputs/module1/`: final Module 1 presentation assets
- `outputs/module1/scratch/`: Unity scratch captures used to build the final presentation board

## Core Docs

- [docs/README.md](docs/README.md): entry point for active documentation
- [docs/01_Project_Status.md](docs/01_Project_Status.md): current module-by-module status
- [docs/02_Pipeline_Guide.md](docs/02_Pipeline_Guide.md): pipeline flow and outputs
- [docs/03_SUMO_Simulation.md](docs/03_SUMO_Simulation.md): SUMO usage and current limitations
- [docs/22_Yeoksam_SUMO_Baseline.md](docs/22_Yeoksam_SUMO_Baseline.md): the simplest assignment-aligned SUMO path

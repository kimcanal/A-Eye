# A-Eye: Taxi Demand Prediction & Dispatch Simulation

A-Eye is a taxi demand forecasting and dispatch simulation project for the **Kakao Mobility Capstone**.

## Current Scope

- **Baseline demand prediction**: Seoul public transit demand is fetched, transformed, and used to train a stable RandomForest baseline.
- **Experimental deep learning path**: A custom ConvLSTM runs on a synthetic 3x3 hotspot grid for spatio-temporal experiments.
- **Dispatch ranking**: Dispatch recommendations are currently generated from the refreshed baseline prediction output.
- **Simulation bridge**: SUMO route files are generated from ConvLSTM output as a coarse simulation demo.

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

This fetches Seoul public data, builds features, refreshes the baseline prediction used by dispatch, trains the ConvLSTM experiment, and exports SUMO routes.

```bash
bash scripts/run_public_pipeline.sh
```

### 3. Optional: Launch SUMO

```bash
cd module1_sumo
sumo-gui -c sumo_config.sumocfg
```

### 4. Optional: Clean generated files

If the generated CSV/PNG/JSON files feel too noisy during development:

```bash
bash scripts/clean_generated_outputs.sh
```

## Core Docs

- [docs/README.md](docs/README.md): entry point for active documentation
- [docs/01_Project_Status.md](docs/01_Project_Status.md): current module-by-module status
- [docs/02_Pipeline_Guide.md](docs/02_Pipeline_Guide.md): pipeline flow and outputs
- [docs/03_SUMO_Simulation.md](docs/03_SUMO_Simulation.md): SUMO usage and current limitations

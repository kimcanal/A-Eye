# A-Eye: Taxi Demand Prediction & Dispatch Simulation

A-Eye is an end-to-end taxi demand forecasting and digital twin simulation framework for the **Kakao Mobility Capstone** project.

## 🚀 Key Features

- **Seoul Public Data Integration**: Fetches real-time transit demand and merges with weather/holiday features.
- **3x3 Grid Spatio-Temporal Modeling**: Synthetically disaggregates dong-level demand for advanced spatial prediction.
- **Custom ConvLSTM (from scratch)**: Proprietary PyTorch implementation of the `ConvLSTM` architecture for grid-based demand prediction.
- **Incentive-Based Dispatch Ranking**: Multi-threshold rule-based dispatch for supply-demand balancing.
- **Standard Simulation (SUMO & Unity)**: Maps predictions to the industrial-standard SUMO traffic simulator and custom Unity digital twin.

---

## 🛠️ Project Structure

- `src/`: Core Python modules (Data, Preprocessing, Prediction, Dispatch, Analysis, Visualization).
- `docs/`: Simplified documentation (Status, Pipeline Guide, SUMO Simulation).
- `module1_sumo/`: SUMO 3x3 Grid simulation files.
- `module1_simulation/`: Unity minimal simulation logic.
- `configs/`: YAML-based configuration for multiple scenarios.
- `scripts/`: Shell scripts for end-to-end pipeline execution.

---

## 🚦 Quick Start

### 1. Configure the environment
Set your Seoul Open API key in your `.zshrc` (or `.bashrc`):
```bash
export SEOUL_OPEN_API_KEY="your_api_key_here"
```

### 2. Run the Full Pipeline
Fetches data, trains the ConvLSTM, and generates SUMO simulation files:
```bash
bash scripts/run_public_pipeline.sh
```

### 3. Launch SUMO Simulation
Verify predictions in the traffic GUI:
```bash
cd module1_sumo
sumo-gui -c sumo_config.sumocfg
```

---

## 📊 Core Documentation

- [01_Project_Status.md](docs/01_Project_Status.md): Feature mapping and assignment checklist.
- [02_Pipeline_Guide.md](docs/02_Pipeline_Guide.md): Detailed instruction for the Python codebase.
- [03_SUMO_Simulation.md](docs/03_SUMO_Simulation.md): How to work with traffic simulation.

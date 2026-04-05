# Project Status: A-Eye (Taxi Demand Prediction & Dispatch Simulation)

## 📋 Assignment Requirements Mapping

| Module | Requirement | Status | Implementation Detail |
| :--- | :--- | :--- | :--- |
| **Module 1** | Digital Twin Simulation | **95%** | Unity-based minimal simulation and SUMO (Standard) integration. |
| **Module 2** | Data Pipeline & External Features | **100%** | Seoul Open API (Transit Demand) + Weather + Holiday features. |
| **Module 3** | Deep Learning Prediction | **100%** | **ConvLSTM (Custom)** architecture for 3x3 Grid prediction + MAPE metrics. |
| **Module 4** | Dispatch Optimization | **90%** | Imbalance-score based rule-based dispatch and incentive multipliers. |

---

## ✅ Major Milestones Completed

### 1. Spatio-Temporal Data Transformation
- We successfully converted administrative district data (1D) into a **3x3 Spatial Grid (2D)**.
- This allows the model to learn spatial dependencies (neighboring cell interactions) which is a core requirement of the assignment.

### 2. Custom ConvLSTM Architecture
- Instead of using a black-box library, we implemented the `ConvLSTMCell` using PyTorch from scratch.
- **Performance**: Achieved stable convergence on Apple Silicon (MPS) and calculated required **MAPE** metrics.

### 3. Data-Driven Simulation
- The simulation no longer uses random spawning. It reads the `dispatch_recommendations.csv` or ConvLSTM predictions to distribute taxi density across the map.

---

## 🛠️ Next Steps / Remaining Tasks
- [ ] **Full SUMO Integration**: Complete the export script to run industrial-standard traffic simulations.
- [ ] **Refine Incentive Logic**: Potentially implement a more complex reinforcement learning or heuristic for the multipliers.
- [ ] **Final Presentation Prep**: Visualize the 3x3 grid demand heatmaps.

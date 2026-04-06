# Project Status: A-Eye (Taxi Demand Prediction & Dispatch Simulation)

## Assignment Requirements Mapping

| Module | Requirement | Status | Implementation Detail |
| :--- | :--- | :--- | :--- |
| **Module 1** | Digital Twin / Simulation | **70%** | Unity minimal simulation exists, and SUMO route export is connected, but SUMO routing is still coarse. |
| **Module 2** | Data Pipeline & Features | **80%** | Seoul Open API fetch/transform works. Holiday and weather scaffolding exist, but weather is still mock-generated. |
| **Module 3** | Prediction | **75%** | RandomForest baseline is stable. ConvLSTM is implemented and runnable, but still experimental. |
| **Module 4** | Dispatch | **80%** | Rule-based dispatch works using refreshed baseline predictions; ConvLSTM-to-dispatch is not yet the main path. |

---

## What Is Working Well

### 1. Public Data Pipeline
- Seoul public transit data can be fetched and transformed into a time-series demand table.
- Administrative dong codes are now resolved into readable names using a Seoul dong master lookup.
- The end-to-end public pipeline completes without manual intervention.

### 2. Stable Baseline Path
- A RandomForest baseline produces reproducible demand predictions.
- Dispatch recommendations are generated from the baseline output and evaluated against a simple allocation baseline.

### 3. Experimental Spatial Path
- A hotspot zone can be expanded into a synthetic 3x3 grid.
- A custom ConvLSTM can train on that grid and export a SUMO route file.

---

## Current Gaps

- ConvLSTM predictions are not yet the main input used by the dispatch module.
- SUMO export currently converts prediction volume into vehicle counts, but not into realistic cell-by-cell routes.
- Weather is still mock-generated, not fetched from a real weather API.
- Dependency reproducibility needs attention on fresh environments.

## Near-Term Next Steps

- [ ] Keep the baseline path stable and reproducible.
- [ ] Make SUMO export more spatially meaningful.
- [ ] Replace mock weather with real external data.
- [ ] Revisit ConvLSTM once the data granularity improves.

# Project Summary

A-Eye is a capstone project focused on taxi demand prediction and dynamic dispatch for a mobility platform.

## Current implementation status

### Module 1 — Digital Twin Environment
- Minimal scenario scaffold completed.
- City size, object counts, and asset requirements are documented.
- Full 3D simulation runtime is not implemented yet.

### Module 2 — Spatio-temporal preprocessing
- Time-based features are implemented.
- Lag and rolling demand features are implemented.
- Feature flags are now read from `configs/base.yaml`.

### Module 3 — Demand prediction
- Baseline model pipeline exists.
- Time-order train/test split is used.
- RMSE and MAE are reported.

### Module 4 — Dispatch logic
- Imbalance scoring is implemented.
- Incentive multiplier rules are implemented.

## Repository structure
- `module1_simulation/`: Module 1 scaffold
- `src/`: pipeline code
- `docs/`: project documentation
- `planning/`: planning notes
- `REPORT.md`: implementation summary

## Next work
1. Expand Module 1 into a runnable simulation.
2. Add MAPE and more visual diagnostics to Module 3.
3. Improve Module 4 explanation and scenario linkage.
4. Align folder naming more closely with the assignment spec if needed.

### Asset analysis
- A downloaded 3D asset pack has been unpacked and the Kakaomobility Unity packages relevant to Module 1 were identified.

### Module 1 results analysis
- Module 1 now runs end-to-end in a minimal scaffold and produces JSON logs plus a summary file.

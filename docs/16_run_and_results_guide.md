# Run and Results Guide

## 1. What currently works

The current Capstone prototype supports the following offline flow:

1. Generate a local taxi demand dataset
2. Build time-series features
3. Train a baseline RandomForest demand model
4. Compute rule-based dispatch priorities from the latest predicted demand
5. Save demand plots and summary CSV files

This is the current "Phase 1" runnable baseline.

## 2. How to run the project

From the project root:

```bash
cd /Users/kenny31/Documents/Capstone
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_pipeline.sh
```

If the virtual environment already exists, only run:

```bash
cd /Users/kenny31/Documents/Capstone
source .venv/bin/activate
bash scripts/run_pipeline.sh
```

## 3. Main outputs

The pipeline generates these files under `outputs/`.

- `processed_taxi_calls.csv`: preprocessed dataset with engineered features
- `model_metrics.json`: baseline model metrics
- `predictions.csv`: actual vs predicted demand values for the test split
- `dispatch_recommendations.csv`: dispatch priority ranking by zone
- `hourly_demand.png`: hourly total demand plot
- `zone_hour_heatmap.png`: average demand heatmap by zone and hour
- `actual_vs_predicted.png`: actual vs predicted demand plot
- `zone_demand_summary.csv`: zone-level demand summary
- `hourly_demand_summary.csv`: hour-level demand summary

Module 1 also writes:

- `outputs/module1/module1_summary.json`
- `outputs/module1/module1_simulation_log.json`

## 4. Result interpretation

### model_metrics.json

Current content:

```json
{
  "model": "random_forest",
  "rows": 640,
  "train_rows": 512,
  "test_rows": 128,
  "features": [
    "available_taxis",
    "pickup_latitude",
    "pickup_longitude",
    "hour",
    "day_of_week",
    "lag_1",
    "rolling_mean_3"
  ],
  "rmse": 2.1358,
  "mae": 1.476
}
```

How to read it:

- `rows = 640`: total usable samples after preprocessing
- `train_rows = 512`, `test_rows = 128`: time-ordered split for training and evaluation
- `features`: the model uses supply, location, and time-series features together
- `rmse = 2.1358`: on average, the prediction error magnitude is a little above 2 calls
- `mae = 1.476`: the average absolute prediction error is about 1.5 calls

This is acceptable for a small synthetic Phase 1 dataset. It means the baseline pipeline is behaving sensibly.

### predictions.csv

This file stores row-level prediction results.

Example:

- `2026-03-22 16:00:00, B, actual 10, predicted 10.21`
- `2026-03-22 18:00:00, A, actual 36, predicted 32.68`

Interpretation:

- Off-peak periods are predicted quite closely
- Peak demand is still slightly underpredicted in some zones
- This gives a clear baseline for later LSTM or CNN-LSTM comparison

### dispatch_recommendations.csv

Current dispatch file now includes:

- `observed_call_count`
- `predicted_call_count`
- `dispatch_demand`
- `demand_source`

Interpretation:

- `demand_source = predicted` means dispatch used the model prediction
- `dispatch_demand` is the demand value actually used in the imbalance calculation
- `observed_call_count` is kept for comparison against the model estimate

Example interpretation:

- A zone can have moderate observed demand but still rank high if predicted demand is higher than supply
- `imbalance_score = dispatch_demand / supply`
- `incentive_multiplier` translates that score into a suggested dispatch incentive

This means the current Phase 1 pipeline is no longer just "predict and dispatch separately"; it now uses the latest prediction output as the dispatch input when predictions are available.

### zone_demand_summary.csv

Current pattern:

- `A` has the highest total demand
- `B` is second
- `C`, `D` follow

Interpretation:

- Zone `A` is the busiest overall zone in the synthetic dataset
- Even if `B` is top priority at the latest step, `A` remains the long-term hotspot
- This distinction is useful: one file explains overall demand, the other explains immediate dispatch priority

### hourly_demand_summary.csv

Current pattern:

- Demand peaks around `08:00-09:00`
- Demand rises again around `18:00-21:00`

Interpretation:

- The dataset reflects commute-style peaks
- This supports the dispatch logic and provides an easy story for presentation

## 5. Module 1 JSON outputs

### module1_summary.json

Current values:

- city size: `3 x 3`
- passengers: `5`
- taxis: `3`
- regular vehicles: `4 types x 5 each`
- autonomous vehicles: `1`
- obstacles: `2`
- steps: `5`
- total entities: `31`

Interpretation:

- This is a minimal stub scenario, not a full simulation engine
- Its purpose is to prove that Module 1 has a runnable structure and machine-readable outputs

### module1_simulation_log.json

This file stores step-by-step simulation snapshots:

- entity counts per step
- movement events
- per-entity positions

Interpretation:

- It is currently useful for documentation, debugging, and future Unity integration
- It is not yet connected to the Python demand prediction pipeline

## 6. What does not work yet

- `train_lstm.py` requires PyTorch and is not part of the default pipeline yet
- public dataset integration is implemented, but still uses a proxy supply value
- real-time external data is not integrated yet
- Unity execution is documented, but not verified end-to-end in this repo

## 7. Recommended next steps

1. Keep this baseline as the stable Phase 1 reference point
2. Improve dispatch evaluation with before/after comparison logic
3. Add weather, holiday, or traffic features to the public pipeline
4. Compare baseline vs LSTM
5. Connect final outputs to Unity visualization

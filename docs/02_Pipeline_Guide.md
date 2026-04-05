# Pipeline Execution Guide: A-Eye

This guide explains how to run the full A-Eye data-to-prediction pipeline using the Seoul Public Transit dataset.

## 🚀 One-Command Execution

The easiest way to run the entire project (Fetch -> Transform -> Preprocess -> Predict) is:

```bash
# Ensure your SEOUL_OPEN_API_KEY is in your .zshrc or environment
bash scripts/run_public_pipeline.sh
```

---

## 🔍 Detailed Stages

### 1. Data Fetch & Transform
- `src.data.fetch_seoul_transit_demand`: Fetches 1,000-row chunks from the Seoul Open API.
- `src.data.transform_seoul_transit_demand`: Cleans and filters for the most recent 30-day window.

### 2. Feature Engineering
- `src.preprocessing.build_features`: Adds time-lag features, rolling means, **Holiday features**, and **Weather mock features**.

### 3. Spatial Grid Generation
- `src.data.generate_grid_dataset`: Takes the top-demand zone (Hotspot) and artificially disaggregates it into a **3x3 grid (9 cells)**.

### 4. Deep Learning Prediction (ConvLSTM)
- `src.prediction.train_convlstm`:
  - Custom PyTorch implementation of **ConvLSTMCell**.
  - Learns spatio-temporal dynamics from the 3x3 grids.
  - Outputs metrics including **MAPE**.

### 5. Dispatch Recommendation
- `src.dispatch.rule_based_dispatch`: Calculates imbalance scores and generates a rank-ordered list of zones for reallocation.

---

## 📊 Outputs

- **Metrics**: `outputs/seoul_public/convlstm_metrics.json`
- **Predictions**: `outputs/seoul_public/convlstm_predictions.csv`
- **Recommendations**: `outputs/seoul_public/dispatch_recommendations.csv`
- **Visuals**: `outputs/seoul_public/*.png`

# Pipeline Execution Guide: A-Eye

This guide explains how to run the full A-Eye data-to-prediction pipeline using the Seoul Public Transit dataset.

## 🚀 One-Command Execution

The easiest way to run the current public-data pipeline is:

```bash
# Ensure your SEOUL_OPEN_API_KEY is in your .zshrc or environment
bash scripts/run_public_pipeline.sh
```

---

## 🔍 Detailed Stages

### 1. Data Fetch & Transform
- `src.data.fetch_seoul_transit_demand`: Fetches 1,000-row chunks from the Seoul Open API.
- `src.data.fetch_seoul_dong_master`: Fetches the Seoul administrative-dong master used to resolve human-readable names.
- `src.data.transform_seoul_transit_demand`: Cleans and filters for the most recent 30-day window, then joins `zone_id` with `zone_name`, `gu_name`, and `full_zone_name`.

### 2. Feature Engineering
- `src.preprocessing.build_features`: Adds time-lag features, rolling means, holiday features, and currently mock weather features.

### 3. Stable Baseline Prediction
- `src.prediction.train_baseline`:
  - Trains a RandomForest baseline on the processed public dataset.
  - Produces `outputs/seoul_public/predictions.csv`.
  - This is the prediction file currently used by the dispatch module.

### 4. Spatial Grid Generation
- `src.data.generate_grid_dataset`: Takes the top-demand zone (Hotspot) and artificially disaggregates it into a **3x3 grid (9 cells)**.

### 5. Deep Learning Prediction (ConvLSTM)
- `src.prediction.train_convlstm`:
  - Custom PyTorch implementation of **ConvLSTMCell**.
  - Learns spatio-temporal dynamics from the 3x3 grids.
  - Outputs metrics including **MAPE**.
  - This is currently an experimental branch, not the primary dispatch input.

### 6. Dispatch Recommendation
- `src.dispatch.rule_based_dispatch`: Calculates imbalance scores and generates a rank-ordered list of zones for reallocation using the baseline prediction file.

### 7. SUMO Export
- `src.dispatch.export_to_sumo`: Converts ConvLSTM output into a coarse SUMO route file for simulation experiments.

---

## 📊 Outputs

- **Baseline metrics**: `outputs/seoul_public/model_metrics.json`
- **Baseline predictions**: `outputs/seoul_public/predictions.csv`
- **ConvLSTM metrics**: `outputs/seoul_public/convlstm_metrics.json`
- **ConvLSTM predictions**: `outputs/seoul_public/convlstm_predictions.csv`
- **Dispatch recommendations**: `outputs/seoul_public/dispatch_recommendations.csv`
- **Readable zone lookup**: `data/seoul_public/zone_lookup.csv`
- **SUMO route file**: `module1_sumo/demand.rou.xml`
- **Visuals**: `outputs/seoul_public/*.png`

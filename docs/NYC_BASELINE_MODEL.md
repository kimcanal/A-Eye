# NYC Baseline Demand Model

This is the first trainable baseline for the A-Eye demand project.
It uses real NYC TLC 5-minute taxi pickup labels to predict taxi demand
`t+5min` at the Manhattan taxi-zone level.

## Split

- Train: `2025-01 through month before 2026-03`
- Test: `2026-03`
- Training sample rows: `1,500,000`
- Test rows: `615,963`

## Metrics

| Model | MAE | RMSE | sMAPE | R2 | Top-5 overlap |
|---|---:|---:|---:|---:|---:|
| Ridge baseline | 1.727561 | 2.837388 | 0.780111 | 0.874927 | 0.618147 |
| Persistence baseline | 2.068444 | 3.431293 | 0.57078 | 0.817088 | 0.566775 |
| Rolling 1h baseline | 1.843877 | 3.171872 | 0.689659 | 0.843701 | 0.605937 |

## Use In A-Eye

This proves the project can train and evaluate a real `t -> t+5min`
taxi-demand model when exact pickup labels exist. Gangnam still remains
a relative heatmap dry test because exact Kakao Taxi pickup labels are not
available in the public dataset.

## Outputs

- `models/nyc_baseline_ridge_model.json`
- `data/processed/model/nyc_baseline_metrics.json`
- `data/processed/model/nyc_baseline_prediction_sample.csv`

## Figures

- `data/processed/model/figures/nyc_baseline_metrics.svg`
- `data/processed/model/figures/nyc_hourly_pattern.svg`
- `data/processed/model/figures/nyc_actual_vs_predicted.svg`
- `data/processed/model/figures/nyc_error_by_zone_type.svg`

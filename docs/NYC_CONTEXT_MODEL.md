# NYC Context-Aware Demand Model

This model joins real NYC taxi pickup labels with weather, US holiday,
and Manhattan subway ridership features.

## Metrics

| Model | MAE | RMSE | sMAPE | R2 | Top-5 overlap |
|---|---:|---:|---:|---:|---:|
| Context Ridge | 1.72876 | 2.834096 | 0.754854 | 0.875217 | 0.617901 |
| Previous Ridge baseline | 1.727561 | 2.837388 | 0.780111 | 0.874927 | 0.618147 |

## Delta

- MAE delta: `0.001199`
- RMSE delta: `-0.003292`
- sMAPE delta: `-0.025257`
- R2 delta: `0.00029`
- Top-5 overlap delta: `-0.000246`

## Context Feature Coefficients

| Feature | Standardized coefficient |
|---|---:|
| subway_ridership | 0.23358067 |
| log_subway_ridership | 0.12249624 |
| subway_transfers | -0.0438594 |

## Interpretation

Recent taxi demand remains the strongest short-horizon predictor. Context
features provide explainability and scenario signals, but they may only
modestly improve a 5-minute horizon because the lagged taxi signal is already
very strong.

Subway ridership is the strongest added context feature by standardized
coefficient, while weather and holiday signals are weaker at the 5-minute
horizon. This is still useful for the A-Eye story: public mobility pressure can
be joined to real taxi labels, but exact Gangnam taxi labels are required before
claiming exact Gangnam taxi counts.

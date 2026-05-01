# Gangnam 5-Minute Demand Prior

Month: `202603`
NYC ratio source: `nyc_tlc_yellow_202501_202603_manhattan`

## Method

Gangnam public data is hourly, so it cannot directly prove exact 5-minute taxi demand.
NYC TLC Yellow Taxi data is used only as a temporal-shape prior inside each hour.

Formula:

```text
Gangnam hourly relative demand pressure x NYC 5-minute slot ratio
= Gangnam 5-minute relative demand prior
```

## Outputs

- `data/processed/demand/nyc_tlc_5min_slot_ratios_202603.csv`
- `data/processed/demand/gangnam_hourly_relative_demand_202603.csv`
- `data/processed/demand/gangnam_5min_relative_demand_prior_202603.csv`
- `data/processed/demand/latest_5min_prediction.json`

## Latest Timestamp Top Dongs

Timestamp: `2026-03-31 23:55:00`

| Rank | Dong | 3D map | Relative score |
|---:|---|---|---:|
| 1 | 역삼1동 | True | 1.0 |
| 2 | 논현1동 | True | 0.46174996 |
| 3 | 삼성2동 | True | 0.36491202 |
| 4 | 압구정동 | False | 0.31664581 |
| 5 | 대치4동 | True | 0.29939748 |

## Safe Claim

This result estimates relative demand direction and heatmap intensity, not exact
Gangnam taxi pickup counts.

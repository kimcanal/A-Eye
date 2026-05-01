# Gangnam Context Transfer Heatmap

Month: `202603`

## Purpose

This table transfers the NYC context-aware result into Gangnam as a relative
5-minute heatmap signal. It keeps the safe project claim: Gangnam has no exact
Kakao Taxi pickup labels, so this is not exact passenger-count prediction.

## Method

1. Start from the Gangnam hourly public-feature prior.
2. Split each hour with the NYC TLC 5-minute temporal slot ratio.
3. Apply the NYC context model conclusion: public-transit pressure is the
   strongest added context signal, while weather/calendar signals are weaker
   at a 5-minute horizon.
4. Normalize by timestamp for Three.js heatmap rendering.

## NYC-Derived Context Weights

- Subway/public-transit boost weight: `0.31118946`
- Weather boost weight: `0.01654777`
- Calendar boost weight: `0.02226277`
- Subway net standardized coefficient: `0.3122175`

US federal holidays are included in the NYC context model. The Gangnam transfer
currently uses the Gangnam CSV weekend flag as a calendar proxy because a Korean
holiday table is not yet part of the local feature set.

## Outputs

- `data/processed/demand/gangnam_context_transfer_5min_202603.csv`
- `data/processed/demand/latest_context_transfer_prediction.json`
- `data/processed/model/nyc_context_metrics.json`

## Latest Timestamp Top Dongs

Timestamp: `2026-03-31 23:55:00`

| Rank | Dong | 3D map | Relative score | Transit signal |
|---:|---|---|---:|---:|
| 1 | 역삼1동 | True | 1.0 | 1.0 |
| 2 | 논현1동 | True | 0.41457599 | 0.56953676 |
| 3 | 삼성2동 | True | 0.30951815 | 0.36039166 |
| 4 | 압구정동 | False | 0.25847129 | 0.22589534 |
| 5 | 대치4동 | True | 0.24091982 | 0.17703306 |

## Safe Claim

NYC proves that real taxi labels can be matched with weather, holiday, and
public-transit context. The Gangnam output transfers that learned tendency
into a relative heatmap, because exact Gangnam taxi call labels are not present.

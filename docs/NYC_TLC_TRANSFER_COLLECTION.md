# NYC TLC Collection Report

## Collected Files

- `raw/nyc_tlc/yellow_tripdata_2025-01.parquet` through
  `raw/nyc_tlc/yellow_tripdata_2026-03.parquet`
  - official NYC TLC Yellow Taxi Trip Records
  - collected in `../a-eye-us-taxi-transfer`
- `raw/nyc_tlc/taxi_zone_lookup.csv`
  - official NYC TLC zone lookup table

## Generated Files

- `processed/nyc_yellow_2025_01_2026_03_manhattan_5min_training_tplus5.parquet`
  - model-ready 5-minute pickup table with `t+5min` and `t+10min` targets
- `processed/nyc_yellow_2025_01_2026_03_manhattan_5min_slot_ratios.csv`
  - compact 12-slot inside-hour ratios for Gangnam 5-minute prior
- `processed/nyc_yellow_2025_01_2026_03_manhattan_zone_type_5min_slot_ratios.csv`
  - slot ratios split by rough Manhattan zone archetype
- `processed/nyc_yellow_2025_01_2026_03_manhattan_zone_type_map.csv`
  - rough zone archetypes for transfer framing
- `processed/nyc_yellow_2025_01_2026_03_manhattan_summary.json`
  - machine-readable collection summary

## Summary

- Month range: `2025-01` to `2026-03`
- Area filter: `Manhattan`
- 5-minute demand rows: `9,041,760`
- training rows: `9,041,691`
- Manhattan taxi zones: `69`
- Pickup time span: `2025-01-01 00:00:00` to `2026-03-31 23:55:00`
- Total pickups in filtered table: `51,302,073`
- Max pickups in one 5-minute zone bucket: `125`

Top pickup zones:

| Rank | Zone | Type | Pickups |
|---:|---|---|---:|
| 1 | Upper East Side South | residential_mixed | 2,605,386 |
| 2 | Midtown Center | business_core | 2,537,018 |
| 3 | Upper East Side North | residential_mixed | 2,324,490 |
| 4 | Penn Station/Madison Sq West | transit_hub | 1,873,774 |
| 5 | Midtown East | business_core | 1,838,193 |

## A-Eye Use

Use this as the real taxi-label side of the project:

- learn or demonstrate `t -> t+5min` pickup-demand prediction
- compare weekday/weekend, commute/lunch/evening/late-night patterns
- pretrain or sanity-check a temporal demand model before applying the Gangnam
  public-data dry test

Keep the claim narrow:

- NYC data gives real 5-minute taxi pickup labels.
- Gangnam data gives public-data features and proxy/relative demand.
- The transfer story is about tendency and heatmap ranking, not exact Gangnam
  passenger counts.

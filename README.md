# A-Eye

Data-first workspace for the Kakao Mobility capstone:

> AI-based taxi demand prediction and dynamic dispatch for a Gangnam micro area.

This repository has been reset to keep the active work data-first.
The current work starts from real and open datasets only.

## Current Position

We do not have exact Kakao Taxi call logs, exact pickup longitude/latitude, or
exact Gangnam taxi pickup counts.

So the project target is:

- predict relative demand rise by Gangnam administrative dong or micro-zone
- show the result as a 5-minute or 1-hour-ahead heatmap
- use the heatmap as the input signal for dispatch-priority visualization

The project should not claim exact passenger-count prediction for Gangnam.

## Current Data

- `data/processed/gangnam_ultimate_dataset.csv`
  - Gangnam dong-hour public-data feature table
  - living population by gender/age
  - weather
  - business category counts
  - weekday/weekend
  - subway daily-average alighting proxy
  - average traffic speed
- `data/processed/transit/`
  - Gangnam/Yeoksam-area Seoul public-transport OD and subway hourly profiles
  - generated from local raw files in `../a-eye-raw-data/seoul-raw`
- `data/processed/demand/`
  - Gangnam hourly relative demand and 5-minute heatmap prior
  - uses 15 months of NYC TLC Manhattan taxi data as a temporal-shape prior
  - full NYC collection workspace lives in `../a-eye-us-taxi-transfer`

## Intended Pipeline

1. Validate and document the Gangnam feature dataset.
2. Build a proxy/relative demand score for Gangnam.
3. Use NYC TLC taxi data to demonstrate real `t -> t+5min` demand labels.
4. Train or sanity-check a temporal model on real 5-minute taxi pickup patterns.
5. Apply the framing to Gangnam as relative demand heatmap prediction.
6. Export heatmap JSON for the Three.js digital twin in `../__yeoksam_taxi`.

## Useful Commands

```bash
python3 scripts/profile_gangnam_dataset.py
python3 scripts/build_gangnam_transit_profile.py --month 202603
python3 scripts/build_gangnam_5min_prior.py --month 202603
```

The profile outputs are written to:

```text
data/processed/transit/
docs/GANGNAM_TRANSIT_COLLECTION.md
data/processed/demand/
docs/GANGNAM_5MIN_PRIOR.md
```

## Related Workspaces

- `../a-eye-raw-data`: collected Seoul public raw data snapshots
- `../a-eye-us-taxi-transfer`: NYC TLC real 5-minute taxi-demand transfer data
- `../__yeoksam_taxi`: Three.js digital-twin visualization
- `../A-Eye_legacy_backup_20260501_230111`: backup of the removed old A-Eye state

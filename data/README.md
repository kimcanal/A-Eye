# Data

This folder is the source of truth for the current A-Eye data work.

## Folders

- `processed/`
  - cleaned or merged project datasets
- `raw/`
  - local raw downloads; ignored by git because raw files can be large

## Main Dataset

`processed/gangnam_ultimate_dataset.csv`

This is a Gangnam dong-hour feature table, not a taxi-call ground-truth table.

Safe interpretation:

- input features for relative demand prediction
- administrative-dong level heatmap dry test
- public-data proxy for mobility pressure
- 5-minute relative demand prior after combining local hourly features with
  NYC TLC temporal slot ratios

Unsafe interpretation:

- exact taxi pickup counts
- exact pickup/dropoff coordinates
- direct Kakao Taxi operational demand

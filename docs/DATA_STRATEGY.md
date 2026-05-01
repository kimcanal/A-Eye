# Data Strategy

## Decision

The current A-Eye path starts from data collection and demand framing.

The old prototype baseline has been removed from the active workspace because
it did not reflect the current team direction.

## Problem

The assignment asks for taxi demand prediction and dynamic dispatch. However,
we do not have:

- Kakao Taxi call logs
- exact pickup longitude/latitude in Gangnam
- exact 5-minute Gangnam taxi pickup counts

## Practical Target

Use the Gangnam public-data feature table to predict:

- which dong or micro-zone is likely to become hotter
- relative demand score
- heatmap ranking

This is a dry test, not an operational taxi-demand model.

## Why NYC TLC Exists In The Project

NYC TLC provides real taxi trip records with pickup time and pickup zone.
That lets us build a real `5-minute pickup_count` target table.

We use it for:

- understanding real taxi temporal demand shape
- `t -> t+5min` model structure
- pretraining or sanity-checking sequence models

We do not use it to claim exact Gangnam demand.

## Gangnam Feature Groups

- time: hour, weekday, weekend
- population: total living population, gender/age population
- weather: temperature, precipitation
- place type: business category counts
- transit proxy: subway daily-average alighting
- traffic proxy: average road speed

## Output To Build Next

- `data/processed/demand/gangnam_hourly_relative_demand_202603.csv`
- `data/processed/demand/gangnam_5min_relative_demand_prior_202603.csv`
- `data/processed/demand/latest_5min_prediction.json`

The JSON output should be shaped so `../__yeoksam_taxi` can read it as a
demand overlay.

# Public Data Quickstart

## Selected public dataset

Main dataset:

- Seoul public data `서울시 행정동별 대중교통 총 승차 승객수 정보`
- Service name: `tpssPassengerCnt`
- Dataset page: https://data.seoul.go.kr/dataList/OA-21223/S/1/datasetView.do

Why this was selected:

- `1 day x 1 hour` granularity
- `행정동` spatial unit
- updated daily
- fits the assignment's Module 2 and Module 3 structure well

## What was added to the repo

- `src/data/fetch_seoul_transit_demand.py`
- `src/data/transform_seoul_transit_demand.py`
- `configs/seoul_public.yaml`
- `scripts/run_public_pipeline.sh`

## How to run with sample data

The Seoul Open API supports a `sample` key, but it only returns up to 5 rows.

```bash
cd /Users/kenny31/Documents/Capstone
source .venv/bin/activate
bash scripts/run_public_pipeline.sh
```

This is useful for:

- schema validation
- transformation testing
- pipeline dry runs

Outputs are saved under:

- `data/seoul_public/`
- `outputs/seoul_public/`

## How to run with a real API key

If the team gets a Seoul Open API key:

```bash
export SEOUL_OPEN_API_KEY=YOUR_KEY_HERE
cd /Users/kenny31/Documents/Capstone
source .venv/bin/activate
bash scripts/run_public_pipeline.sh
```

With a real key, the fetcher will request the full dataset in pages of 1000 rows.

## Important limitation

This dataset contains demand only.

It does **not** contain:

- available taxis
- empty taxi supply
- live driver positions

So the current transformer creates a deterministic `available_taxis` proxy to keep Module 4 runnable.

That means:

- forecasting becomes public-data based
- dispatch is still partly heuristic until real supply data is added

## Current public-data schema after transform

The transformed file looks like this:

- `pickup_datetime`
- `zone_id`
- `call_count`
- `available_taxis`
- `source_total_passengers`

This matches the existing Phase 1 pipeline closely enough to reuse the current preprocessing, prediction, dispatch, and visualization code.

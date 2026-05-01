# NYC Context Feature Join

This builds the feature-rich NYC training table that mirrors the Gangnam
feature strategy: real taxi demand labels joined with weather, holidays,
and public-transit pressure.

## Sources

- NYC TLC Yellow Taxi Trip Records
  - https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Open-Meteo Historical Weather API
  - https://open-meteo.com/en/docs/historical-weather-api
- MTA Subway Hourly Ridership: Beginning 2025
  - https://data.ny.gov/d/5wq4-mkjj
- US federal holiday calendar generated deterministically in code

## Generated Files

- `a-eye-us-taxi-transfer/processed/nyc_weather_hourly_2025_01_2026_03.csv`
- `a-eye-us-taxi-transfer/processed/nyc_mta_manhattan_subway_hourly_2025_01_2026_03.csv`
- `a-eye-us-taxi-transfer/processed/us_federal_holidays_hourly_2025_01_2026_03.csv`
- `a-eye-us-taxi-transfer/processed/nyc_yellow_2025_01_2026_03_manhattan_context_training_tplus5.parquet`
- `data/processed/model/nyc_context_feature_summary.json`

## Join Quality

- Missing weather rows: `0`
- Missing subway rows: `828`
- Missing holiday rows: `0`

The missing subway rows correspond to one 5-minute taxi-grid hour during the
March daylight-saving-time transition (`69 zones x 12 five-minute slots = 828`).
The model fills that hour with `0` for the subway feature.

## Safe Interpretation

The subway feature is a Manhattan-wide hourly public-transit pressure proxy.
It is not yet a precise station-to-taxi-zone spatial join. That can be added
later with taxi zone polygons and station coordinates.

from __future__ import annotations

import argparse
import calendar
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
NYC_TRANSFER_DIR = WORKSPACE_DIR / "a-eye-us-taxi-transfer"
NYC_PYTHON_PACKAGES = NYC_TRANSFER_DIR / ".python-packages"
NYC_PROCESSED_DIR = NYC_TRANSFER_DIR / "processed"
NYC_TAXI_TRAINING = (
    NYC_PROCESSED_DIR / "nyc_yellow_2025_01_2026_03_manhattan_5min_training_tplus5.parquet"
)
WEATHER_CSV = NYC_PROCESSED_DIR / "nyc_weather_hourly_2025_01_2026_03.csv"
SUBWAY_CSV = NYC_PROCESSED_DIR / "nyc_mta_manhattan_subway_hourly_2025_01_2026_03.csv"
HOLIDAY_CSV = NYC_PROCESSED_DIR / "us_federal_holidays_hourly_2025_01_2026_03.csv"
ENRICHED_PARQUET = (
    NYC_PROCESSED_DIR / "nyc_yellow_2025_01_2026_03_manhattan_context_training_tplus5.parquet"
)
SUMMARY_JSON = ROOT_DIR / "data" / "processed" / "model" / "nyc_context_feature_summary.json"
REPORT_PATH = ROOT_DIR / "docs" / "NYC_CONTEXT_FEATURES.md"

START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 3, 31)
END_EXCLUSIVE = END_DATE + timedelta(days=1)
NYC_LATITUDE = 40.7831
NYC_LONGITUDE = -73.9712
MTA_2025_DATASET = "5wq4-mkjj"

if NYC_PYTHON_PACKAGES.exists():
    sys.path.insert(0, str(NYC_PYTHON_PACKAGES))

try:
    import duckdb
except ImportError as exc:
    raise SystemExit("duckdb is required. Build the NYC transfer workspace first.") from exc


def sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def observed_date(value: date) -> date:
    if value.weekday() == 5:
        return value - timedelta(days=1)
    if value.weekday() == 6:
        return value + timedelta(days=1)
    return value


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    day = date(year, month, 1)
    while day.weekday() != weekday:
        day += timedelta(days=1)
    return day + timedelta(days=7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    day = date(year, month, calendar.monthrange(year, month)[1])
    while day.weekday() != weekday:
        day -= timedelta(days=1)
    return day


def federal_holidays(year: int) -> dict[date, str]:
    holidays = {
        observed_date(date(year, 1, 1)): "New Year's Day",
        nth_weekday(year, 1, 0, 3): "Martin Luther King Jr. Day",
        nth_weekday(year, 2, 0, 3): "Washington's Birthday",
        last_weekday(year, 5, 0): "Memorial Day",
        observed_date(date(year, 6, 19)): "Juneteenth National Independence Day",
        observed_date(date(year, 7, 4)): "Independence Day",
        nth_weekday(year, 9, 0, 1): "Labor Day",
        nth_weekday(year, 10, 0, 2): "Columbus Day",
        observed_date(date(year, 11, 11)): "Veterans Day",
        nth_weekday(year, 11, 3, 4): "Thanksgiving Day",
        observed_date(date(year, 12, 25)): "Christmas Day",
    }
    return holidays


def build_holiday_rows() -> list[dict[str, object]]:
    holidays: dict[date, str] = {}
    for year in {START_DATE.year, END_DATE.year}:
        holidays.update(federal_holidays(year))
    holiday_dates = set(holidays)
    rows: list[dict[str, object]] = []
    current = datetime.combine(START_DATE, datetime.min.time())
    end = datetime.combine(END_EXCLUSIVE, datetime.min.time())
    while current < end:
        current_date = current.date()
        rows.append(
            {
                "hour_ts": current.strftime("%Y-%m-%d %H:%M:%S"),
                "service_date": current_date.isoformat(),
                "is_us_federal_holiday": int(current_date in holiday_dates),
                "holiday_name": holidays.get(current_date, ""),
                "is_day_before_holiday": int(current_date + timedelta(days=1) in holiday_dates),
                "is_day_after_holiday": int(current_date - timedelta(days=1) in holiday_dates),
            }
        )
        current += timedelta(hours=1)
    return rows


def fetch_weather(force: bool) -> list[dict[str, object]]:
    if WEATHER_CSV.exists() and not force:
        with WEATHER_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    params = {
        "latitude": str(NYC_LATITUDE),
        "longitude": str(NYC_LONGITUDE),
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "hourly": "temperature_2m,precipitation,wind_speed_10m,weather_code",
        "timezone": "America/New_York",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urlencode(params)
    payload = json.loads(urlopen(url, timeout=120).read().decode("utf-8"))
    hourly = payload["hourly"]
    rows: list[dict[str, object]] = []
    for index, time_value in enumerate(hourly["time"]):
        ts = datetime.strptime(time_value, "%Y-%m-%dT%H:%M")
        precipitation = hourly["precipitation"][index] or 0
        rows.append(
            {
                "hour_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature_2m_c": hourly["temperature_2m"][index],
                "precipitation_mm": precipitation,
                "wind_speed_10m_kmh": hourly["wind_speed_10m"][index],
                "weather_code": hourly["weather_code"][index],
                "is_rain": int(float(precipitation) > 0),
            }
        )
    write_csv(
        WEATHER_CSV,
        [
            "hour_ts",
            "temperature_2m_c",
            "precipitation_mm",
            "wind_speed_10m_kmh",
            "weather_code",
            "is_rain",
        ],
        rows,
    )
    return rows


def fetch_subway(force: bool) -> list[dict[str, object]]:
    if SUBWAY_CSV.exists() and not force:
        with SUBWAY_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    params = {
        "$select": (
            "transit_timestamp,"
            "sum(ridership) as subway_ridership,"
            "sum(transfers) as subway_transfers"
        ),
        "$where": (
            f"transit_timestamp between '{START_DATE.isoformat()}T00:00:00' "
            f"and '{END_EXCLUSIVE.isoformat()}T00:00:00' "
            "AND borough='Manhattan' AND transit_mode='subway'"
        ),
        "$group": "transit_timestamp",
        "$order": "transit_timestamp",
        "$limit": "50000",
    }
    url = f"https://data.ny.gov/resource/{MTA_2025_DATASET}.json?" + urlencode(params)
    data = json.loads(urlopen(url, timeout=180).read().decode("utf-8"))
    rows: list[dict[str, object]] = []
    for row in data:
        ts = datetime.strptime(row["transit_timestamp"][:19], "%Y-%m-%dT%H:%M:%S")
        rows.append(
            {
                "hour_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "subway_ridership": round(float(row.get("subway_ridership") or 0), 4),
                "subway_transfers": round(float(row.get("subway_transfers") or 0), 4),
            }
        )
    write_csv(SUBWAY_CSV, ["hour_ts", "subway_ridership", "subway_transfers"], rows)
    return rows


def write_holidays(force: bool) -> list[dict[str, object]]:
    if HOLIDAY_CSV.exists() and not force:
        with HOLIDAY_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    rows = build_holiday_rows()
    write_csv(
        HOLIDAY_CSV,
        [
            "hour_ts",
            "service_date",
            "is_us_federal_holiday",
            "holiday_name",
            "is_day_before_holiday",
            "is_day_after_holiday",
        ],
        rows,
    )
    return rows


def build_enriched_parquet() -> dict[str, object]:
    con = duckdb.connect()
    con.execute("set threads to 4")
    con.execute(
        f"""
        create or replace temp view taxi as
        select
          *,
          date_trunc('hour', pickup_5min) as hour_ts
        from read_parquet({sql_literal(NYC_TAXI_TRAINING)})
        """
    )
    con.execute(
        f"""
        create or replace temp view weather as
        select
          cast(hour_ts as timestamp) as hour_ts,
          cast(temperature_2m_c as double) as temperature_2m_c,
          cast(precipitation_mm as double) as precipitation_mm,
          cast(wind_speed_10m_kmh as double) as wind_speed_10m_kmh,
          cast(weather_code as integer) as weather_code,
          cast(is_rain as integer) as is_rain
        from read_csv_auto({sql_literal(WEATHER_CSV)})
        """
    )
    con.execute(
        f"""
        create or replace temp view subway as
        select
          cast(hour_ts as timestamp) as hour_ts,
          cast(subway_ridership as double) as subway_ridership,
          cast(subway_transfers as double) as subway_transfers
        from read_csv_auto({sql_literal(SUBWAY_CSV)})
        """
    )
    con.execute(
        f"""
        create or replace temp view holidays as
        select
          cast(hour_ts as timestamp) as hour_ts,
          cast(is_us_federal_holiday as integer) as is_us_federal_holiday,
          holiday_name,
          cast(is_day_before_holiday as integer) as is_day_before_holiday,
          cast(is_day_after_holiday as integer) as is_day_after_holiday
        from read_csv_auto({sql_literal(HOLIDAY_CSV)})
        """
    )
    con.execute(
        """
        create or replace temp view enriched as
        select
          taxi.* exclude(hour_ts),
          taxi.hour_ts,
          coalesce(weather.temperature_2m_c, 0) as temperature_2m_c,
          coalesce(weather.precipitation_mm, 0) as precipitation_mm,
          coalesce(weather.wind_speed_10m_kmh, 0) as wind_speed_10m_kmh,
          coalesce(weather.weather_code, 0) as weather_code,
          coalesce(weather.is_rain, 0) as is_rain,
          coalesce(subway.subway_ridership, 0) as subway_ridership,
          coalesce(subway.subway_transfers, 0) as subway_transfers,
          ln(1 + coalesce(subway.subway_ridership, 0)) as log_subway_ridership,
          coalesce(holidays.is_us_federal_holiday, 0) as is_us_federal_holiday,
          coalesce(holidays.holiday_name, '') as holiday_name,
          coalesce(holidays.is_day_before_holiday, 0) as is_day_before_holiday,
          coalesce(holidays.is_day_after_holiday, 0) as is_day_after_holiday
        from taxi
        left join weather on taxi.hour_ts = weather.hour_ts
        left join subway on taxi.hour_ts = subway.hour_ts
        left join holidays on taxi.hour_ts = holidays.hour_ts
        """
    )
    con.execute(
        f"""
        copy enriched to {sql_literal(ENRICHED_PARQUET)}
        (format parquet, compression zstd)
        """
    )
    stats = con.execute(
        """
        select
          count(*)::bigint,
          min(pickup_5min)::varchar,
          max(pickup_5min)::varchar,
          count(distinct hour_ts)::integer,
          avg(temperature_2m_c)::double,
          sum(is_rain)::bigint,
          avg(subway_ridership)::double,
          sum(is_us_federal_holiday)::bigint
        from enriched
        """
    ).fetchone()
    missing = con.execute(
        """
        select
          sum(case when weather.hour_ts is null then 1 else 0 end)::bigint as missing_weather_rows,
          sum(case when subway.hour_ts is null then 1 else 0 end)::bigint as missing_subway_rows,
          sum(case when holidays.hour_ts is null then 1 else 0 end)::bigint as missing_holiday_rows
        from taxi
        left join weather on taxi.hour_ts = weather.hour_ts
        left join subway on taxi.hour_ts = subway.hour_ts
        left join holidays on taxi.hour_ts = holidays.hour_ts
        """
    ).fetchone()
    con.close()
    return {
        "enriched_training_parquet": str(ENRICHED_PARQUET.relative_to(WORKSPACE_DIR)),
        "stats": {
            "rows": stats[0],
            "first_pickup_5min": stats[1],
            "last_pickup_5min": stats[2],
            "hour_count": stats[3],
            "avg_temperature_2m_c": round(float(stats[4] or 0), 4),
            "rain_rows": stats[5],
            "avg_subway_ridership_hour": round(float(stats[6] or 0), 4),
            "holiday_rows": stats[7],
        },
        "join_quality": {
            "missing_weather_rows": missing[0],
            "missing_subway_rows": missing[1],
            "missing_holiday_rows": missing[2],
        },
    }


def write_report(summary: dict[str, object]) -> None:
    lines = [
        "# NYC Context Feature Join",
        "",
        "This builds the feature-rich NYC training table that mirrors the Gangnam",
        "feature strategy: real taxi demand labels joined with weather, holidays,",
        "and public-transit pressure.",
        "",
        "## Sources",
        "",
        "- NYC TLC Yellow Taxi Trip Records",
        "  - https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
        "- Open-Meteo Historical Weather API",
        "  - https://open-meteo.com/en/docs/historical-weather-api",
        "- MTA Subway Hourly Ridership: Beginning 2025",
        "  - https://data.ny.gov/d/5wq4-mkjj",
        "- US federal holiday calendar generated deterministically in code",
        "",
        "## Generated Files",
        "",
        f"- `{WEATHER_CSV.relative_to(WORKSPACE_DIR)}`",
        f"- `{SUBWAY_CSV.relative_to(WORKSPACE_DIR)}`",
        f"- `{HOLIDAY_CSV.relative_to(WORKSPACE_DIR)}`",
        f"- `{ENRICHED_PARQUET.relative_to(WORKSPACE_DIR)}`",
        f"- `{SUMMARY_JSON.relative_to(ROOT_DIR)}`",
        "",
        "## Join Quality",
        "",
        f"- Missing weather rows: `{summary['join_quality']['missing_weather_rows']}`",
        f"- Missing subway rows: `{summary['join_quality']['missing_subway_rows']}`",
        f"- Missing holiday rows: `{summary['join_quality']['missing_holiday_rows']}`",
        "",
        "The missing subway rows correspond to one 5-minute taxi-grid hour during the",
        "March daylight-saving-time transition (`69 zones x 12 five-minute slots = 828`).",
        "The model fills that hour with `0` for the subway feature.",
        "",
        "## Safe Interpretation",
        "",
        "The subway feature is a Manhattan-wide hourly public-transit pressure proxy.",
        "It is not yet a precise station-to-taxi-zone spatial join. That can be added",
        "later with taxi zone polygons and station coordinates.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    weather_rows = fetch_weather(args.force_download)
    subway_rows = fetch_subway(args.force_download)
    holiday_rows = write_holidays(args.force_download)
    enriched = build_enriched_parquet()
    summary = {
        "sources": {
            "weather": "Open-Meteo Historical Weather API",
            "subway": "MTA Subway Hourly Ridership: Beginning 2025",
            "holidays": "US federal holiday calendar",
            "taxi": "NYC TLC Yellow Taxi Trip Records",
        },
        "raw_feature_rows": {
            "weather_hourly": len(weather_rows),
            "subway_hourly": len(subway_rows),
            "holiday_hourly": len(holiday_rows),
        },
        **enriched,
    }
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()

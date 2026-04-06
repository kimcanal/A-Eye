from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from src.data.fetch_seoul_dong_master import DONG_MASTER_CSV, ensure_dong_master_csv

OUTPUT_CSV = Path("data/seoul_public/transit_demand_long.csv")
ZONE_LOOKUP_CSV = Path("data/seoul_public/zone_lookup.csv")


def compute_supply(call_count: float) -> int:
    # Public data gives demand only, so we use a deterministic proxy supply
    # to keep the dispatch module runnable until real supply data is added.
    base = round(call_count * 0.55)
    return max(1, int(base))


def main() -> None:
    raw_input_env = os.environ.get("SEOUL_TRANSIT_RAW_JSON")
    if raw_input_env:
        raw_input = Path(raw_input_env)
    else:
        candidates = sorted(Path("data/seoul_public/raw").glob("tpssPassengerCnt_*.json"))
        if not candidates:
            raise SystemExit("Missing raw input under data/seoul_public/raw. Run fetch_seoul_transit_demand first.")
        custom_candidates = [path for path in candidates if path.stem.endswith("_custom")]
        raw_input = custom_candidates[-1] if custom_candidates else candidates[-1]

    payload = json.loads(raw_input.read_text(encoding="utf-8"))
    rows = payload["rows"]
    api_key_type = payload.get("api_key_type", "unknown")

    recent_days_env = os.environ.get("SEOUL_TRANSIT_RECENT_DAYS")
    recent_days = int(recent_days_env) if recent_days_env else None

    if recent_days is None and api_key_type == "custom":
        # Full public data spans years. Keep the default training slice small
        # enough for local baseline experiments unless the user overrides it.
        recent_days = 30

    if recent_days is not None and rows:
        latest_date = max(row["CRTR_DD"] for row in rows)
        latest_ts = pd.Timestamp(
            year=int(latest_date[0:4]),
            month=int(latest_date[4:6]),
            day=int(latest_date[6:8]),
        )
        cutoff = latest_ts - pd.Timedelta(days=recent_days - 1)
        rows = [
            row
            for row in rows
            if pd.Timestamp(
                year=int(row["CRTR_DD"][0:4]),
                month=int(row["CRTR_DD"][4:6]),
                day=int(row["CRTR_DD"][6:8]),
            ) >= cutoff
        ]

    records: list[dict] = []
    for row in rows:
        date_str = row["CRTR_DD"]
        for hour in range(24):
            demand = float(row[f"PSNG_NO_{hour:02d}"])
            ts = pd.Timestamp(
                year=int(date_str[0:4]),
                month=int(date_str[4:6]),
                day=int(date_str[6:8]),
                hour=hour,
            )
            records.append(
                {
                    "pickup_datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "zone_id": str(row["DONG_ID"]),
                    "call_count": demand,
                    "available_taxis": compute_supply(demand),
                    "source_total_passengers": float(row["PSNG_NO"]),
                }
            )

    df = pd.DataFrame(records).sort_values(["zone_id", "pickup_datetime"]).reset_index(drop=True)

    master_csv_env = os.environ.get("SEOUL_DONG_MASTER_CSV")
    master_csv = Path(master_csv_env) if master_csv_env else DONG_MASTER_CSV
    master_csv = ensure_dong_master_csv(master_csv)

    master_df = pd.read_csv(master_csv, dtype={"zone_id": str})
    df["zone_id"] = df["zone_id"].astype(str)
    df = df.merge(master_df, on="zone_id", how="left")
    df["zone_name"] = df["zone_name"].fillna(df["zone_id"])
    df["gu_name"] = df["gu_name"].fillna("unknown")
    df["city_name"] = df["city_name"].fillna("unknown")
    df["full_zone_name"] = df["full_zone_name"].fillna(df["zone_name"])

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    zone_lookup = (
        df[["zone_id", "zone_name", "gu_name", "city_name", "full_zone_name"]]
        .drop_duplicates()
        .sort_values(["gu_name", "zone_name", "zone_id"])
        .reset_index(drop=True)
    )
    zone_lookup.to_csv(ZONE_LOOKUP_CSV, index=False)

    print(f"saved: {OUTPUT_CSV}")
    print(f"saved: {ZONE_LOOKUP_CSV}")
    print(f"rows: {len(df)}")
    print(f"source: {raw_input}")
    print(f"dong_master: {master_csv}")
    if recent_days is not None:
        print(f"recent_days: {recent_days}")


if __name__ == "__main__":
    main()

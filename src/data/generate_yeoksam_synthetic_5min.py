from __future__ import annotations

from math import sin, pi
from pathlib import Path

import pandas as pd

from src.common.config import load_config


ZONE_META = [
    ("A1", "Yeoksam NW Office", "Teheran-ro west office cluster"),
    ("A2", "Teheran West", "Teheran corridor approach"),
    ("A3", "Teheran East", "Teheran east office cluster"),
    ("B1", "Yeoksam West", "Residential and side-street pickup area"),
    ("B2", "Gangnam Station Core", "Primary hotspot around Gangnam Station"),
    ("B3", "Yeoksam East Commercial", "Commercial pickup spillover"),
    ("C1", "Yeoksam SW", "Lower-demand residential zone"),
    ("C2", "Gangnam-daero South", "Secondary hotspot toward main boulevard"),
    ("C3", "Yeoksam SE", "Mixed office-residential zone"),
]

BASE_WEIGHTS = {
    "A1": 0.65,
    "A2": 1.05,
    "A3": 0.8,
    "B1": 0.75,
    "B2": 1.8,
    "B3": 1.2,
    "C1": 0.55,
    "C2": 1.25,
    "C3": 0.7,
}

SUPPLY_WEIGHTS = {
    "A1": 0.75,
    "A2": 0.95,
    "A3": 0.85,
    "B1": 0.8,
    "B2": 1.15,
    "B3": 1.0,
    "C1": 0.65,
    "C2": 0.95,
    "C3": 0.75,
}


def demand_level(step_index: int, period_count: int) -> float:
    """Synthetic Friday evening wave: center peak around the middle of the horizon."""
    progress = step_index / max(period_count - 1, 1)
    evening_wave = 1.0 + 0.35 * sin(progress * pi)
    late_peak = 1.0 + 0.25 * sin(progress * 2 * pi - pi / 4)
    return evening_wave * late_peak


def build_dataset(cfg: dict) -> pd.DataFrame:
    start = pd.Timestamp(cfg["yeoksam"]["start"])
    periods = int(cfg["yeoksam"]["periods"])
    freq_minutes = int(cfg["yeoksam"]["freq_minutes"])
    timestamps = pd.date_range(start=start, periods=periods, freq=f"{freq_minutes}min")

    records: list[dict] = []
    for step_index, ts in enumerate(timestamps):
        wave = demand_level(step_index, periods)
        for zone_id, zone_name, zone_desc in ZONE_META:
            base = BASE_WEIGHTS[zone_id]
            supply_base = SUPPLY_WEIGHTS[zone_id]

            office_drop = 1.15 if zone_id in {"A2", "A3", "B2"} else 1.0
            station_spike = 1.2 if zone_id in {"B2", "C2", "B3"} and ts.hour >= 19 else 1.0
            quiet_bias = 0.85 if zone_id in {"C1", "A1"} and ts.hour >= 23 else 1.0

            demand = max(1, round(5 * base * wave * office_drop * station_spike * quiet_bias))
            supply = max(1, round(4 * supply_base * (1.0 + 0.15 * sin(step_index / 6.0))))

            records.append(
                {
                    "pickup_datetime": ts,
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "full_zone_name": f"Yeoksam 3x3 {zone_id} - {zone_desc}",
                    "call_count": demand,
                    "available_taxis": supply,
                }
            )

    return pd.DataFrame(records)


def main() -> None:
    cfg = load_config()
    output_csv = Path(cfg["yeoksam"]["output_csv"])
    df = build_dataset(cfg)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"saved: {output_csv}")
    print(f"rows: {len(df)}")
    print(f"zones: {df['zone_id'].nunique()}")
    print(
        "time_range:",
        df["pickup_datetime"].min(),
        "->",
        df["pickup_datetime"].max(),
    )


if __name__ == "__main__":
    main()

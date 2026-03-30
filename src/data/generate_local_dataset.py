from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def build_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    timestamps = pd.date_range("2026-03-17 07:00:00", "2026-03-23 23:00:00", freq="1h")
    zone_specs = {
        "A": {"base": 18, "lat": 37.4981, "lon": 127.0276, "peak_bonus": 14},
        "B": {"base": 12, "lat": 37.5012, "lon": 127.0396, "peak_bonus": 8},
        "C": {"base": 9, "lat": 37.4922, "lon": 127.0411, "peak_bonus": 5},
        "D": {"base": 7, "lat": 37.4871, "lon": 127.0304, "peak_bonus": 3},
    }
    rows: list[dict] = []

    for ts in timestamps:
        for zone_id, spec in zone_specs.items():
            hour = ts.hour
            weekend = ts.dayofweek >= 5
            peak = 1 if hour in {8, 9, 18, 19, 20, 21} else 0
            weather_penalty = 2 if ts.day == 20 else 0
            weekend_bonus = 3 if weekend and hour >= 18 else 0
            noise = rng.integers(-2, 3)

            demand = max(
                1,
                spec["base"] + peak * spec["peak_bonus"] + weekend_bonus - weather_penalty + int(noise),
            )
            supply = max(1, int(round(demand * rng.uniform(0.35, 0.75))))

            rows.append(
                {
                    "pickup_datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "zone_id": zone_id,
                    "call_count": demand,
                    "available_taxis": supply,
                    "pickup_latitude": spec["lat"],
                    "pickup_longitude": spec["lon"],
                }
            )

    return pd.DataFrame(rows)


def main() -> None:
    output = Path("data/local_taxi_calls.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    df = build_dataset()
    df.to_csv(output, index=False)
    print(f"saved: {output} ({len(df)} rows)")


if __name__ == "__main__":
    main()

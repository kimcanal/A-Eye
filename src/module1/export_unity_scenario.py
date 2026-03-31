#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from datetime import datetime, UTC
from pathlib import Path


CAPSTONE_ROOT = Path("/Users/kenny31/Documents/Capstone")
DEFAULT_OUTPUT = CAPSTONE_ROOT / "outputs" / "module1" / "unity_scenario.json"
PUBLIC_DISPATCH = CAPSTONE_ROOT / "outputs" / "seoul_public" / "dispatch_recommendations.csv"
LOCAL_DISPATCH = CAPSTONE_ROOT / "outputs" / "dispatch_recommendations.csv"

TAXI_SLOTS = [
    {
        "name": "Taxi_A",
        "hotspot_label": "West Gate",
        "position": {"x": -8.0, "y": 0.15, "z": -12.0},
        "rotation_y": 0.0,
    },
    {
        "name": "Taxi_B",
        "hotspot_label": "South Hub",
        "position": {"x": 4.0, "y": 0.15, "z": -12.0},
        "rotation_y": 180.0,
    },
    {
        "name": "Taxi_C",
        "hotspot_label": "East Connector",
        "position": {"x": 12.0, "y": 0.15, "z": 6.0},
        "rotation_y": -90.0,
    },
]

OBSTACLE_SLOTS = [
    {
        "name": "Obstacle_Cone_A",
        "prefab_key": "cone",
        "position": {"x": -2.0, "y": 0.02, "z": -4.0},
        "rotation_y": 0.0,
    },
    {
        "name": "Obstacle_Cone_B",
        "prefab_key": "cone_alt",
        "position": {"x": -1.0, "y": 0.02, "z": -4.5},
        "rotation_y": 0.0,
    },
    {
        "name": "Obstacle_Bollard",
        "prefab_key": "bollard",
        "position": {"x": 6.0, "y": 0.02, "z": 3.0},
        "rotation_y": 0.0,
    },
    {
        "name": "Obstacle_Fence",
        "prefab_key": "fence",
        "position": {"x": 10.0, "y": 0.02, "z": -2.0},
        "rotation_y": 90.0,
    },
]


def choose_dispatch_csv() -> Path:
    if PUBLIC_DISPATCH.exists():
        return PUBLIC_DISPATCH
    if LOCAL_DISPATCH.exists():
        return LOCAL_DISPATCH
    raise FileNotFoundError("No dispatch recommendations CSV found.")


def load_top_dispatch_rows(path: Path, limit: int = 3) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    rows.sort(key=lambda row: int(float(row["dispatch_rank"])))
    return rows[:limit]


def maybe_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def build_scenario(rows: list[dict[str, str]], source_csv: Path) -> dict:
    taxis: list[dict] = []
    for slot, row in zip(TAXI_SLOTS, rows):
        taxis.append(
            {
                "name": slot["name"],
                "zone_id": row.get("zone_id"),
                "dispatch_rank": int(float(row["dispatch_rank"])),
                "hotspot_label": slot["hotspot_label"],
                "pickup_datetime": row.get("pickup_datetime"),
                "dispatch_demand": maybe_float(row.get("dispatch_demand")),
                "predicted_call_count": maybe_float(row.get("predicted_call_count")),
                "observed_call_count": maybe_float(row.get("observed_call_count")),
                "available_taxis": maybe_float(row.get("available_taxis")),
                "imbalance_score": maybe_float(row.get("imbalance_score")),
                "incentive_multiplier": maybe_float(row.get("incentive_multiplier")),
                "position": slot["position"],
                "rotation_y": slot["rotation_y"],
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_csv": str(source_csv),
        "mapping_note": "Zone priority is mapped to fixed demo slots in the Unity city scene.",
        "taxis": taxis,
        "obstacles": OBSTACLE_SLOTS,
    }


def main() -> None:
    source_csv = choose_dispatch_csv()
    rows = load_top_dispatch_rows(source_csv)
    scenario = build_scenario(rows, source_csv)
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved Unity scenario: {DEFAULT_OUTPUT}")


if __name__ == "__main__":
    main()

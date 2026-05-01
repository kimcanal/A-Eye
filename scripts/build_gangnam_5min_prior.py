from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
GANGNAM_DATASET = ROOT_DIR / "data" / "processed" / "gangnam_ultimate_dataset.csv"
TARGET_DONGS_JSON = ROOT_DIR / "data" / "target_gangnam_dongs.json"
TRANSIT_SUMMARY = ROOT_DIR / "data" / "processed" / "transit" / "gangnam_transit_od_hourly_summary_202603.csv"
SUBWAY_SUMMARY = ROOT_DIR / "data" / "processed" / "transit" / "gangnam_subway_dong_hourly_summary_202603.csv"
NYC_TRANSFER_PROCESSED = WORKSPACE_DIR / "a-eye-us-taxi-transfer" / "processed"
OUTPUT_DIR = ROOT_DIR / "data" / "processed" / "demand"
DOC_PATH = ROOT_DIR / "docs" / "GANGNAM_5MIN_PRIOR.md"

BUSINESS_COLUMNS = [
    "과학·기술",
    "교육",
    "보건의료",
    "부동산",
    "소매",
    "수리·개인",
    "숙박",
    "시설관리·임대",
    "예술·스포츠",
    "음식",
]


def number(value: object) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(",", "")
    if not text:
        return 0.0
    return float(text)


def normalize(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    min_value = min(values.values())
    max_value = max(values.values())
    if max_value <= min_value:
        return {key: 0.0 for key in values}
    return {
        key: (value - min_value) / (max_value - min_value)
        for key, value in values.items()
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_target_dongs() -> tuple[list[str], dict[str, int]]:
    data = json.loads(TARGET_DONGS_JSON.read_text(encoding="utf-8"))
    dongs = [dong["dong_name"] for dong in data["dongs"]]
    included = {
        dong["dong_name"]: int(bool(dong["included_in_3d_map"]))
        for dong in data["dongs"]
    }
    return dongs, included


def day_type_from_dow(dow: int) -> str:
    return "weekend" if dow in {0, 6} else "weekday"


def find_latest_nyc_slot_ratio() -> Path | None:
    candidates = sorted(
        NYC_TRANSFER_PROCESSED.glob("nyc_yellow_*_manhattan_5min_slot_ratios.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_precomputed_nyc_slot_ratios(
    path: Path,
) -> tuple[list[dict[str, object]], dict[tuple[str, int, int], float], dict[tuple[int, int], float]]:
    ratio_rows: list[dict[str, object]] = []
    ratio_lookup: dict[tuple[str, int, int], float] = {}
    fallback_counts: dict[tuple[int, int], float] = defaultdict(float)
    fallback_totals: dict[int, float] = defaultdict(float)
    fallback_ratio_sums: dict[tuple[int, int], float] = defaultdict(float)
    fallback_ratio_counts: dict[tuple[int, int], int] = defaultdict(int)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row.get("source") or path.stem
            day_type = row["day_type"]
            hour = int(row["service_hour"])
            slot = int(row["slot_5min"])
            ratio = number(row["slot_ratio"])
            pickup_count = number(row.get("pickup_count"))
            hour_total = number(row.get("hour_total_pickups"))

            ratio_lookup[(day_type, hour, slot)] = ratio
            fallback_counts[(hour, slot)] += pickup_count
            fallback_totals[hour] += pickup_count
            fallback_ratio_sums[(hour, slot)] += ratio
            fallback_ratio_counts[(hour, slot)] += 1
            ratio_rows.append(
                {
                    "source": source,
                    "day_type": day_type,
                    "service_hour": hour,
                    "slot_5min": slot,
                    "minute": slot * 5,
                    "pickup_count": int(pickup_count),
                    "hour_total_pickups": int(hour_total),
                    "slot_ratio": round(ratio, 8),
                }
            )

    fallback_lookup: dict[tuple[int, int], float] = {}
    for hour in range(24):
        total = fallback_totals[hour]
        for slot in range(12):
            if total > 0:
                fallback_lookup[(hour, slot)] = fallback_counts[(hour, slot)] / total
                continue
            count = fallback_ratio_counts[(hour, slot)]
            fallback_lookup[(hour, slot)] = (
                fallback_ratio_sums[(hour, slot)] / count if count else 1 / 12
            )

    return ratio_rows, ratio_lookup, fallback_lookup


def load_nyc_slot_ratios() -> tuple[list[dict[str, object]], dict[tuple[str, int, int], float], dict[tuple[int, int], float]]:
    precomputed_ratio_path = find_latest_nyc_slot_ratio()
    if not precomputed_ratio_path:
        raise SystemExit(
            "Missing NYC 5-minute slot ratio CSV. Run "
            "`PYTHONPATH=.python-packages python3 scripts/build_nyc_multi_month_profile.py "
            "--start-month 2025-01 --end-month 2026-03 --borough Manhattan` "
            "inside ../a-eye-us-taxi-transfer first."
        )
    return load_precomputed_nyc_slot_ratios(precomputed_ratio_path)


def load_transit_feature_tables() -> tuple[dict[tuple[str, int], float], dict[tuple[str, int], float]]:
    transit: dict[tuple[str, int], float] = {}
    subway: dict[tuple[str, int], float] = {}

    with TRANSIT_SUMMARY.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transit[(row["dong_name"], int(row["service_hour"]))] = number(
                row["avg_transit_pressure"]
            )

    with SUBWAY_SUMMARY.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subway[(row["dong_name"], int(row["service_hour"]))] = number(
                row["daily_avg_subway_pressure"]
            )

    return transit, subway


def build_hourly_pressure(month: str) -> list[dict[str, object]]:
    dongs, included = load_target_dongs()
    transit, subway = load_transit_feature_tables()
    month_prefix = month

    duplicate_acc: dict[tuple[str, int, str], dict[str, float]] = defaultdict(
        lambda: {
            "rows": 0,
            "living_population": 0.0,
            "temperature": 0.0,
            "rain": 0.0,
            "business_total": 0.0,
            "subway_daily_alight": 0.0,
            "traffic_speed": 0.0,
            "weekend": 0.0,
            "weekday_raw": 0.0,
        }
    )

    with GANGNAM_DATASET.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row["기준일ID"]
            if not date.startswith(month_prefix):
                continue
            dong_name = row["행정동명"]
            if dong_name not in dongs:
                continue
            hour = int(row["시간대구분"])
            key = (date, hour, dong_name)
            acc = duplicate_acc[key]
            acc["rows"] += 1
            acc["living_population"] += number(row["총생활인구수"])
            acc["temperature"] += number(row["기온"])
            acc["rain"] += number(row["강수량"])
            acc["business_total"] += sum(number(row[column]) for column in BUSINESS_COLUMNS)
            acc["subway_daily_alight"] += number(row["일평균하차인원"])
            acc["traffic_speed"] += number(row["평균통행속도"])
            acc["weekend"] += number(row["주말여부"])
            acc["weekday_raw"] += number(row["요일"])

    averaged_rows: list[dict[str, object]] = []
    for (date, hour, dong_name), acc in sorted(duplicate_acc.items()):
        row_count = max(acc["rows"], 1)
        traffic_speed = acc["traffic_speed"] / row_count
        averaged_rows.append(
            {
                "service_date": date,
                "service_hour": hour,
                "dong_name": dong_name,
                "included_in_3d_map": included[dong_name],
                "day_type": day_type_from_dow(int(round(acc["weekday_raw"] / row_count))),
                "living_population": acc["living_population"] / row_count,
                "temperature": acc["temperature"] / row_count,
                "rain": acc["rain"] / row_count,
                "business_total": acc["business_total"] / row_count,
                "subway_daily_alight": acc["subway_daily_alight"] / row_count,
                "traffic_speed": traffic_speed,
                "traffic_congestion": 1 / traffic_speed if traffic_speed > 0 else 0,
                "transit_pressure": transit.get((dong_name, hour), 0.0),
                "subway_pressure": subway.get((dong_name, hour), 0.0),
            }
        )

    grouped: dict[tuple[str, int], list[dict[str, object]]] = defaultdict(list)
    for row in averaged_rows:
        grouped[(str(row["service_date"]), int(row["service_hour"]))].append(row)

    output_rows: list[dict[str, object]] = []
    for (date, hour), rows in sorted(grouped.items()):
        norm_living = normalize({str(row["dong_name"]): float(row["living_population"]) for row in rows})
        norm_business = normalize({str(row["dong_name"]): float(row["business_total"]) for row in rows})
        norm_subway_alight = normalize({str(row["dong_name"]): float(row["subway_daily_alight"]) for row in rows})
        norm_transit = normalize({str(row["dong_name"]): float(row["transit_pressure"]) for row in rows})
        norm_subway = normalize({str(row["dong_name"]): float(row["subway_pressure"]) for row in rows})
        norm_congestion = normalize({str(row["dong_name"]): float(row["traffic_congestion"]) for row in rows})
        max_rain = max(float(row["rain"]) for row in rows) if rows else 0.0
        rain_signal = min(max_rain / 20.0, 1.0)

        raw_scores: dict[str, float] = {}
        for row in rows:
            dong = str(row["dong_name"])
            commute_weight = 1.0 if hour in {7, 8, 9, 17, 18, 19, 20} else 0.0
            lunch_weight = 1.0 if hour in {12, 13} else 0.0
            late_weight = 1.0 if hour in {22, 23, 0, 1, 2} else 0.0
            raw_score = (
                0.20 * norm_living[dong]
                + 0.20 * norm_transit[dong]
                + 0.18 * norm_subway[dong]
                + 0.12 * norm_subway_alight[dong]
                + 0.12 * norm_business[dong]
                + 0.08 * norm_congestion[dong]
                + 0.05 * commute_weight
                + 0.03 * lunch_weight
                + 0.02 * late_weight
                + 0.05 * rain_signal
            )
            raw_scores[dong] = raw_score

        total_raw = sum(raw_scores.values())
        for row in rows:
            dong = str(row["dong_name"])
            relative = raw_scores[dong] / total_raw if total_raw > 0 else 1 / len(rows)
            output_rows.append(
                {
                    **row,
                    "hourly_raw_score": round(raw_scores[dong], 8),
                    "hourly_relative_demand": round(relative, 8),
                }
            )

    return output_rows


def split_to_5min(
    hourly_rows: list[dict[str, object]],
    ratio_lookup: dict[tuple[str, int, int], float],
    fallback_lookup: dict[tuple[int, int], float],
) -> list[dict[str, object]]:
    rows_5min: list[dict[str, object]] = []
    for row in hourly_rows:
        date = str(row["service_date"])
        hour = int(row["service_hour"])
        day_type = str(row["day_type"])
        base_time = datetime.strptime(f"{date}{hour:02d}00", "%Y%m%d%H%M")
        for slot in range(12):
            ratio = ratio_lookup.get((day_type, hour, slot), fallback_lookup.get((hour, slot), 1 / 12))
            timestamp = base_time + timedelta(minutes=slot * 5)
            rows_5min.append(
                {
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "service_date": date,
                    "service_hour": hour,
                    "slot_5min": slot,
                    "minute": slot * 5,
                    "dong_name": row["dong_name"],
                    "included_in_3d_map": row["included_in_3d_map"],
                    "day_type": day_type,
                    "nyc_slot_ratio": round(ratio, 8),
                    "hourly_relative_demand": row["hourly_relative_demand"],
                    "estimated_5min_relative_demand": round(float(row["hourly_relative_demand"]) * ratio, 10),
                    "hourly_raw_score": row["hourly_raw_score"],
                    "transit_pressure": round(float(row["transit_pressure"]), 3),
                    "subway_pressure": round(float(row["subway_pressure"]), 3),
                    "living_population": round(float(row["living_population"]), 4),
                    "rain": round(float(row["rain"]), 4),
                    "traffic_speed": round(float(row["traffic_speed"]), 4),
                }
            )
    return rows_5min


def write_latest_prediction(rows_5min: list[dict[str, object]], output_path: Path) -> dict[str, object]:
    if not rows_5min:
        raise SystemExit("No 5-minute rows generated")
    latest_timestamp = max(str(row["timestamp"]) for row in rows_5min)
    latest_rows = [row for row in rows_5min if row["timestamp"] == latest_timestamp]
    max_score = max(float(row["estimated_5min_relative_demand"]) for row in latest_rows) or 1.0
    ranked_rows = sorted(
        latest_rows,
        key=lambda row: float(row["estimated_5min_relative_demand"]),
        reverse=True,
    )
    payload = {
        "source": "gangnam_hourly_public_features_x_nyc_tlc_5min_slot_ratio",
        "timestamp": latest_timestamp,
        "description": "5-minute relative demand prior for Gangnam dongs. Not exact taxi pickup count.",
        "dongs": [
            {
                "rank": index + 1,
                "dong_name": row["dong_name"],
                "included_in_3d_map": bool(int(row["included_in_3d_map"])),
                "relative_score": round(float(row["estimated_5min_relative_demand"]) / max_score, 8),
                "raw_5min_score": row["estimated_5min_relative_demand"],
                "hourly_relative_demand": row["hourly_relative_demand"],
                "nyc_slot_ratio": row["nyc_slot_ratio"],
                "top_reasons": [
                    "local transit pressure",
                    "subway station pressure",
                    "NYC 5-minute temporal shape prior",
                ],
            }
            for index, row in enumerate(ranked_rows)
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def write_report(
    month: str,
    nyc_ratio_source: str,
    latest_payload: dict[str, object],
    outputs: dict[str, str],
) -> None:
    top = latest_payload["dongs"][:5]
    lines = [
        "# Gangnam 5-Minute Demand Prior",
        "",
        f"Month: `{month}`",
        f"NYC ratio source: `{nyc_ratio_source}`",
        "",
        "## Method",
        "",
        "Gangnam public data is hourly, so it cannot directly prove exact 5-minute taxi demand.",
        "NYC TLC Yellow Taxi data is used only as a temporal-shape prior inside each hour.",
        "",
        "Formula:",
        "",
        "```text",
        "Gangnam hourly relative demand pressure x NYC 5-minute slot ratio",
        "= Gangnam 5-minute relative demand prior",
        "```",
        "",
        "## Outputs",
        "",
        f"- `{outputs['nyc_ratio_csv']}`",
        f"- `{outputs['hourly_csv']}`",
        f"- `{outputs['five_min_csv']}`",
        f"- `{outputs['latest_json']}`",
        "",
        "## Latest Timestamp Top Dongs",
        "",
        f"Timestamp: `{latest_payload['timestamp']}`",
        "",
        "| Rank | Dong | 3D map | Relative score |",
        "|---:|---|---|---:|",
    ]
    for row in top:
        lines.append(
            f"| {row['rank']} | {row['dong_name']} | {row['included_in_3d_map']} | {row['relative_score']} |"
        )
    lines.extend(
        [
            "",
            "## Safe Claim",
            "",
            "This result estimates relative demand direction and heatmap intensity, not exact",
            "Gangnam taxi pickup counts.",
        ]
    )
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", default="202603")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ratio_rows, ratio_lookup, fallback_lookup = load_nyc_slot_ratios()
    nyc_ratio_source = str(ratio_rows[0]["source"]) if ratio_rows else "unknown"
    hourly_rows = build_hourly_pressure(args.month)
    rows_5min = split_to_5min(hourly_rows, ratio_lookup, fallback_lookup)

    nyc_ratio_csv = OUTPUT_DIR / f"nyc_tlc_5min_slot_ratios_{args.month}.csv"
    hourly_csv = OUTPUT_DIR / f"gangnam_hourly_relative_demand_{args.month}.csv"
    five_min_csv = OUTPUT_DIR / f"gangnam_5min_relative_demand_prior_{args.month}.csv"
    latest_json = OUTPUT_DIR / "latest_5min_prediction.json"

    write_csv(
        nyc_ratio_csv,
        [
            "source",
            "day_type",
            "service_hour",
            "slot_5min",
            "minute",
            "pickup_count",
            "hour_total_pickups",
            "slot_ratio",
        ],
        ratio_rows,
    )
    write_csv(
        hourly_csv,
        [
            "service_date",
            "service_hour",
            "dong_name",
            "included_in_3d_map",
            "day_type",
            "living_population",
            "temperature",
            "rain",
            "business_total",
            "subway_daily_alight",
            "traffic_speed",
            "traffic_congestion",
            "transit_pressure",
            "subway_pressure",
            "hourly_raw_score",
            "hourly_relative_demand",
        ],
        hourly_rows,
    )
    write_csv(
        five_min_csv,
        [
            "timestamp",
            "service_date",
            "service_hour",
            "slot_5min",
            "minute",
            "dong_name",
            "included_in_3d_map",
            "day_type",
            "nyc_slot_ratio",
            "hourly_relative_demand",
            "estimated_5min_relative_demand",
            "hourly_raw_score",
            "transit_pressure",
            "subway_pressure",
            "living_population",
            "rain",
            "traffic_speed",
        ],
        rows_5min,
    )
    latest_payload = write_latest_prediction(rows_5min, latest_json)
    outputs = {
        "nyc_ratio_csv": str(nyc_ratio_csv.relative_to(ROOT_DIR)),
        "hourly_csv": str(hourly_csv.relative_to(ROOT_DIR)),
        "five_min_csv": str(five_min_csv.relative_to(ROOT_DIR)),
        "latest_json": str(latest_json.relative_to(ROOT_DIR)),
    }
    write_report(args.month, nyc_ratio_source, latest_payload, outputs)
    print(json.dumps({"outputs": outputs, "latest": latest_payload}, ensure_ascii=False, indent=2))
    print(f"saved report: {DOC_PATH}")


if __name__ == "__main__":
    main()

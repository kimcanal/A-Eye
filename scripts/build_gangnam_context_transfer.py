from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEMAND_DIR = ROOT_DIR / "data" / "processed" / "demand"
MODEL_DIR = ROOT_DIR / "data" / "processed" / "model"
NYC_CONTEXT_METRICS = MODEL_DIR / "nyc_context_metrics.json"
OUTPUT_DOC = ROOT_DIR / "docs" / "GANGNAM_CONTEXT_TRANSFER.md"


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def coefficient_map() -> dict[str, float]:
    payload = json.loads(NYC_CONTEXT_METRICS.read_text(encoding="utf-8"))
    features = payload["model"]["features"]
    coefficients = payload["model"]["coefficients"]
    return {
        str(feature): float(coef)
        for feature, coef in zip(features, coefficients, strict=True)
    }


def context_weights(coefficients: dict[str, float]) -> dict[str, float]:
    subway_net = (
        coefficients.get("subway_ridership", 0.0)
        + coefficients.get("log_subway_ridership", 0.0)
        + coefficients.get("subway_transfers", 0.0)
    )
    weather_strength = sum(
        abs(coefficients.get(feature, 0.0))
        for feature in [
            "temperature_2m_c",
            "precipitation_mm",
            "wind_speed_10m_kmh",
            "is_rain",
        ]
    )
    calendar_strength = sum(
        abs(coefficients.get(feature, 0.0))
        for feature in [
            "is_us_federal_holiday",
            "is_day_before_holiday",
            "is_day_after_holiday",
            "is_weekend",
        ]
    )
    total = max(abs(subway_net) + weather_strength + calendar_strength, 1e-9)
    max_context_boost = 0.35
    return {
        "subway_net_coefficient": round(subway_net, 8),
        "weather_abs_coefficient": round(weather_strength, 8),
        "calendar_abs_coefficient": round(calendar_strength, 8),
        "subway_boost_weight": round(max_context_boost * abs(subway_net) / total, 8),
        "weather_boost_weight": round(max_context_boost * weather_strength / total, 8),
        "calendar_boost_weight": round(max_context_boost * calendar_strength / total, 8),
        "max_context_boost": max_context_boost,
    }


def load_inputs(month: str) -> tuple[list[dict[str, str]], dict[tuple[str, int, str], dict[str, str]]]:
    five_min_path = DEMAND_DIR / f"gangnam_5min_relative_demand_prior_{month}.csv"
    hourly_path = DEMAND_DIR / f"gangnam_hourly_relative_demand_{month}.csv"
    if not five_min_path.exists():
        raise SystemExit(f"Missing 5-minute prior: {five_min_path}")
    if not hourly_path.exists():
        raise SystemExit(f"Missing hourly prior: {hourly_path}")

    hourly_lookup = {
        (row["service_date"], int(row["service_hour"]), row["dong_name"]): row
        for row in read_csv(hourly_path)
    }
    return read_csv(five_min_path), hourly_lookup


def feature_rows_by_timestamp(
    five_min_rows: list[dict[str, str]],
    hourly_lookup: dict[tuple[str, int, str], dict[str, str]],
) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in five_min_rows:
        key = (row["service_date"], int(row["service_hour"]), row["dong_name"])
        hourly = hourly_lookup.get(key)
        if not hourly:
            raise SystemExit(f"Missing hourly feature row for {key}")
        traffic_speed = number(hourly.get("traffic_speed"))
        grouped[row["timestamp"]].append(
            {
                **row,
                "business_total": number(hourly.get("business_total")),
                "subway_daily_alight": number(hourly.get("subway_daily_alight")),
                "traffic_congestion": 1 / traffic_speed if traffic_speed > 0 else 0.0,
            }
        )
    return grouped


def top_reasons(row: dict[str, object]) -> list[str]:
    reasons = ["NYC context model: subway ridership was the strongest added signal"]
    if float(row["public_transit_signal"]) >= 0.67:
        reasons.append("Gangnam local transit/subway pressure is high")
    if float(row["base_heatmap_intensity"]) >= 0.67:
        reasons.append("Gangnam hourly public-feature prior is high")
    if float(row["rain_signal"]) > 0:
        reasons.append("weather signal is present but weak in the 5-minute model")
    if float(row["calendar_signal"]) > 0:
        reasons.append("calendar/weekend signal is present but weaker than transit")
    return reasons[:4]


def build_transfer_rows(month: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    coefficients = coefficient_map()
    weights = context_weights(coefficients)
    five_min_rows, hourly_lookup = load_inputs(month)
    grouped = feature_rows_by_timestamp(five_min_rows, hourly_lookup)

    output_rows: list[dict[str, object]] = []
    for timestamp, rows in sorted(grouped.items()):
        norm_transit = normalize({str(row["dong_name"]): number(row["transit_pressure"]) for row in rows})
        norm_subway = normalize({str(row["dong_name"]): number(row["subway_pressure"]) for row in rows})
        norm_subway_alight = normalize(
            {str(row["dong_name"]): number(row["subway_daily_alight"]) for row in rows}
        )
        norm_business = normalize({str(row["dong_name"]): number(row["business_total"]) for row in rows})
        norm_congestion = normalize({str(row["dong_name"]): number(row["traffic_congestion"]) for row in rows})
        base_scores = {
            str(row["dong_name"]): number(row["estimated_5min_relative_demand"])
            for row in rows
        }
        norm_base = normalize(base_scores)
        max_rain = max(number(row["rain"]) for row in rows) if rows else 0.0
        rain_signal = min(max_rain / 20.0, 1.0)
        calendar_signal = 1.0 if rows and str(rows[0]["day_type"]) == "weekend" else 0.0

        raw_rows: list[dict[str, object]] = []
        for row in rows:
            dong = str(row["dong_name"])
            public_transit_signal = (
                0.50 * norm_subway.get(dong, 0.0)
                + 0.30 * norm_transit.get(dong, 0.0)
                + 0.20 * norm_subway_alight.get(dong, 0.0)
            )
            context_multiplier = (
                1.0
                + float(weights["subway_boost_weight"]) * public_transit_signal
                + float(weights["weather_boost_weight"]) * rain_signal
                + float(weights["calendar_boost_weight"]) * calendar_signal
            )
            spatial_explainability_score = (
                0.46 * public_transit_signal
                + 0.22 * norm_base.get(dong, 0.0)
                + 0.16 * norm_business.get(dong, 0.0)
                + 0.10 * norm_congestion.get(dong, 0.0)
                + 0.04 * rain_signal
                + 0.02 * calendar_signal
            )
            transfer_raw_score = number(row["hourly_relative_demand"]) * context_multiplier
            raw_rows.append(
                {
                    **row,
                    "public_transit_signal": public_transit_signal,
                    "business_signal": norm_business.get(dong, 0.0),
                    "congestion_signal": norm_congestion.get(dong, 0.0),
                    "base_heatmap_intensity": norm_base.get(dong, 0.0),
                    "rain_signal": rain_signal,
                    "calendar_signal": calendar_signal,
                    "context_multiplier": context_multiplier,
                    "spatial_explainability_score": spatial_explainability_score,
                    "transfer_raw_score": transfer_raw_score,
                }
            )

        raw_total = sum(number(row["transfer_raw_score"]) for row in raw_rows)
        slot_ratio = number(raw_rows[0]["nyc_slot_ratio"]) if raw_rows else 0.0
        max_transfer = max(number(row["transfer_raw_score"]) for row in raw_rows) or 1.0
        for row in raw_rows:
            timestamp_share = number(row["transfer_raw_score"]) / raw_total if raw_total > 0 else 0.0
            output_rows.append(
                {
                    "timestamp": row["timestamp"],
                    "service_date": row["service_date"],
                    "service_hour": int(row["service_hour"]),
                    "slot_5min": int(row["slot_5min"]),
                    "minute": int(row["minute"]),
                    "dong_name": row["dong_name"],
                    "included_in_3d_map": int(row["included_in_3d_map"]),
                    "day_type": row["day_type"],
                    "nyc_slot_ratio": round(slot_ratio, 8),
                    "base_5min_relative_demand": round(number(row["estimated_5min_relative_demand"]), 10),
                    "context_multiplier": round(number(row["context_multiplier"]), 8),
                    "context_transfer_share": round(timestamp_share, 10),
                    "context_transfer_5min_prior": round(timestamp_share * slot_ratio, 10),
                    "heatmap_intensity": round(number(row["transfer_raw_score"]) / max_transfer, 8),
                    "spatial_explainability_score": round(number(row["spatial_explainability_score"]), 8),
                    "public_transit_signal": round(number(row["public_transit_signal"]), 8),
                    "business_signal": round(number(row["business_signal"]), 8),
                    "congestion_signal": round(number(row["congestion_signal"]), 8),
                    "base_heatmap_intensity": round(number(row["base_heatmap_intensity"]), 8),
                    "rain_signal": round(number(row["rain_signal"]), 8),
                    "calendar_signal": round(number(row["calendar_signal"]), 8),
                    "transit_pressure": round(number(row["transit_pressure"]), 3),
                    "subway_pressure": round(number(row["subway_pressure"]), 3),
                    "subway_daily_alight": round(number(row["subway_daily_alight"]), 3),
                    "rain": round(number(row["rain"]), 4),
                    "traffic_speed": round(number(row["traffic_speed"]), 4),
                }
            )

    summary = {
        "source": "Gangnam public features + NYC context-aware taxi demand model",
        "month": month,
        "row_count": len(output_rows),
        "timestamp_count": len(grouped),
        "context_weights": weights,
        "calendar_note": (
            "US federal holidays are used in NYC context training. Gangnam transfer currently "
            "uses weekend/calendar proxy because no Korean holiday table is present in the "
            "Gangnam feature CSV."
        ),
        "safe_claim": "Relative Gangnam demand heatmap signal, not exact taxi pickup count.",
    }
    return output_rows, summary


def latest_payload(rows: list[dict[str, object]]) -> dict[str, object]:
    latest_timestamp = max(str(row["timestamp"]) for row in rows)
    latest_rows = [row for row in rows if row["timestamp"] == latest_timestamp]
    ranked = sorted(latest_rows, key=lambda row: number(row["heatmap_intensity"]), reverse=True)
    return {
        "source": "gangnam_public_features_x_nyc_context_transfer",
        "timestamp": latest_timestamp,
        "description": "5-minute Gangnam context-transfer heatmap. Not exact taxi pickup count.",
        "dongs": [
            {
                "rank": index + 1,
                "dong_name": row["dong_name"],
                "included_in_3d_map": bool(int(row["included_in_3d_map"])),
                "relative_score": row["heatmap_intensity"],
                "context_transfer_5min_prior": row["context_transfer_5min_prior"],
                "context_multiplier": row["context_multiplier"],
                "public_transit_signal": row["public_transit_signal"],
                "top_reasons": top_reasons(row),
            }
            for index, row in enumerate(ranked)
        ],
    }


def write_report(month: str, summary: dict[str, object], latest: dict[str, object]) -> None:
    weights = summary["context_weights"]
    lines = [
        "# Gangnam Context Transfer Heatmap",
        "",
        f"Month: `{month}`",
        "",
        "## Purpose",
        "",
        "This table transfers the NYC context-aware result into Gangnam as a relative",
        "5-minute heatmap signal. It keeps the safe project claim: Gangnam has no exact",
        "Kakao Taxi pickup labels, so this is not exact passenger-count prediction.",
        "",
        "## Method",
        "",
        "1. Start from the Gangnam hourly public-feature prior.",
        "2. Split each hour with the NYC TLC 5-minute temporal slot ratio.",
        "3. Apply the NYC context model conclusion: public-transit pressure is the",
        "   strongest added context signal, while weather/calendar signals are weaker",
        "   at a 5-minute horizon.",
        "4. Normalize by timestamp for Three.js heatmap rendering.",
        "",
        "## NYC-Derived Context Weights",
        "",
        f"- Subway/public-transit boost weight: `{weights['subway_boost_weight']}`",
        f"- Weather boost weight: `{weights['weather_boost_weight']}`",
        f"- Calendar boost weight: `{weights['calendar_boost_weight']}`",
        f"- Subway net standardized coefficient: `{weights['subway_net_coefficient']}`",
        "",
        "US federal holidays are included in the NYC context model. The Gangnam transfer",
        "currently uses the Gangnam CSV weekend flag as a calendar proxy because a Korean",
        "holiday table is not yet part of the local feature set.",
        "",
        "## Outputs",
        "",
        f"- `data/processed/demand/gangnam_context_transfer_5min_{month}.csv`",
        "- `data/processed/demand/latest_context_transfer_prediction.json`",
        "- `data/processed/model/nyc_context_metrics.json`",
        "",
        "## Latest Timestamp Top Dongs",
        "",
        f"Timestamp: `{latest['timestamp']}`",
        "",
        "| Rank | Dong | 3D map | Relative score | Transit signal |",
        "|---:|---|---|---:|---:|",
    ]
    for row in latest["dongs"][:5]:
        lines.append(
            "| "
            f"{row['rank']} | {row['dong_name']} | {row['included_in_3d_map']} | "
            f"{row['relative_score']} | {row['public_transit_signal']} |"
        )
    lines.extend(
        [
            "",
            "## Safe Claim",
            "",
            "NYC proves that real taxi labels can be matched with weather, holiday, and",
            "public-transit context. The Gangnam output transfers that learned tendency",
            "into a relative heatmap, because exact Gangnam taxi call labels are not present.",
        ]
    )
    OUTPUT_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", default="202603")
    args = parser.parse_args()

    rows, summary = build_transfer_rows(args.month)
    output_csv = DEMAND_DIR / f"gangnam_context_transfer_5min_{args.month}.csv"
    latest_json = DEMAND_DIR / "latest_context_transfer_prediction.json"
    summary_json = MODEL_DIR / f"gangnam_context_transfer_summary_{args.month}.json"

    write_csv(
        output_csv,
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
            "base_5min_relative_demand",
            "context_multiplier",
            "context_transfer_share",
            "context_transfer_5min_prior",
            "heatmap_intensity",
            "spatial_explainability_score",
            "public_transit_signal",
            "business_signal",
            "congestion_signal",
            "base_heatmap_intensity",
            "rain_signal",
            "calendar_signal",
            "transit_pressure",
            "subway_pressure",
            "subway_daily_alight",
            "rain",
            "traffic_speed",
        ],
        rows,
    )
    latest = latest_payload(rows)
    latest_json.write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["outputs"] = {
        "five_min_csv": str(output_csv.relative_to(ROOT_DIR)),
        "latest_json": str(latest_json.relative_to(ROOT_DIR)),
        "summary_json": str(summary_json.relative_to(ROOT_DIR)),
        "report": str(OUTPUT_DOC.relative_to(ROOT_DIR)),
    }
    summary["latest_top_dongs"] = latest["dongs"][:5]
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(args.month, summary, latest)
    print(json.dumps({"summary": summary, "latest": latest}, ensure_ascii=False, indent=2))
    print(f"saved report: {OUTPUT_DOC}")


if __name__ == "__main__":
    main()

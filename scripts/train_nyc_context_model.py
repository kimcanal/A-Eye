from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
NYC_TRANSFER_DIR = WORKSPACE_DIR / "a-eye-us-taxi-transfer"
NYC_PYTHON_PACKAGES = NYC_TRANSFER_DIR / ".python-packages"
NYC_CONTEXT_PARQUET = (
    NYC_TRANSFER_DIR
    / "processed"
    / "nyc_yellow_2025_01_2026_03_manhattan_context_training_tplus5.parquet"
)
BASELINE_METRIC_PATH = ROOT_DIR / "data" / "processed" / "model" / "nyc_baseline_metrics.json"
MODEL_DIR = ROOT_DIR / "models"
MODEL_PATH = MODEL_DIR / "nyc_context_ridge_model.json"
METRIC_DIR = ROOT_DIR / "data" / "processed" / "model"
METRIC_PATH = METRIC_DIR / "nyc_context_metrics.json"
PREDICTION_SAMPLE_PATH = METRIC_DIR / "nyc_context_prediction_sample.csv"
REPORT_PATH = ROOT_DIR / "docs" / "NYC_CONTEXT_MODEL.md"

if NYC_PYTHON_PACKAGES.exists():
    sys.path.insert(0, str(NYC_PYTHON_PACKAGES))

try:
    import duckdb
except ImportError as exc:
    raise SystemExit("duckdb is required. Build the NYC transfer workspace first.") from exc


ZONE_TYPES = [
    "business_core",
    "commercial_mixed",
    "residential_mixed",
    "transit_hub",
    "urban_mixed",
]

FEATURE_EXPRESSIONS = [
    ("pickup_count", "pickup_count::double"),
    ("lag_t_minus_5", "coalesce(lag_pickup_count_t_minus_5, 0)::double"),
    ("lag_t_minus_15", "coalesce(lag_pickup_count_t_minus_15, 0)::double"),
    ("lag_t_minus_60", "coalesce(lag_pickup_count_t_minus_60, 0)::double"),
    ("rolling_avg_prev_1h", "coalesce(rolling_avg_pickups_prev_1h, 0)::double"),
    ("avg_passenger_count", "coalesce(avg_passenger_count, 0)::double"),
    ("avg_trip_distance_miles", "coalesce(avg_trip_distance_miles, 0)::double"),
    ("is_weekend", "is_weekend::double"),
    ("is_morning_commute", "is_morning_commute::double"),
    ("is_lunch", "is_lunch::double"),
    ("is_evening_peak", "is_evening_peak::double"),
    ("is_late_night", "is_late_night::double"),
    ("hour_sin", "sin(2 * pi() * pickup_hour / 24.0)"),
    ("hour_cos", "cos(2 * pi() * pickup_hour / 24.0)"),
    ("slot_sin", "sin(2 * pi() * slot_5min / 12.0)"),
    ("slot_cos", "cos(2 * pi() * slot_5min / 12.0)"),
    ("dow_sin", "sin(2 * pi() * day_of_week / 7.0)"),
    ("dow_cos", "cos(2 * pi() * day_of_week / 7.0)"),
    ("temperature_2m_c", "coalesce(temperature_2m_c, 0)::double"),
    ("precipitation_mm", "coalesce(precipitation_mm, 0)::double"),
    ("wind_speed_10m_kmh", "coalesce(wind_speed_10m_kmh, 0)::double"),
    ("is_rain", "coalesce(is_rain, 0)::double"),
    ("subway_ridership", "coalesce(subway_ridership, 0)::double"),
    ("subway_transfers", "coalesce(subway_transfers, 0)::double"),
    ("log_subway_ridership", "coalesce(log_subway_ridership, 0)::double"),
    ("is_us_federal_holiday", "coalesce(is_us_federal_holiday, 0)::double"),
    ("is_day_before_holiday", "coalesce(is_day_before_holiday, 0)::double"),
    ("is_day_after_holiday", "coalesce(is_day_after_holiday, 0)::double"),
]

for zone_type in ZONE_TYPES:
    FEATURE_EXPRESSIONS.append(
        (
            f"zone_type_{zone_type}",
            f"case when zone_type = '{zone_type}' then 1.0 else 0.0 end",
        )
    )


def sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def feature_select_sql(include_meta: bool) -> str:
    columns = [f"{expr} as {name}" for name, expr in FEATURE_EXPRESSIONS]
    columns.append("target_pickup_count_t_plus_5::double as target")
    if include_meta:
        columns = [
            "pickup_5min::varchar as pickup_5min",
            "target_5min::varchar as target_5min",
            "pickup_location_id",
            "zone",
            "zone_type",
        ] + columns
    return ",\n          ".join(columns)


def load_matrix(
    con: duckdb.DuckDBPyConnection,
    where_sql: str,
    limit: int | None,
    include_meta: bool = False,
) -> tuple[list[tuple] | None, np.ndarray, np.ndarray]:
    limit_sql = f"limit {limit}" if limit else ""
    rows = con.execute(
        f"""
        select
          {feature_select_sql(include_meta)}
        from read_parquet({sql_literal(NYC_CONTEXT_PARQUET)})
        where {where_sql}
        {limit_sql}
        """
    ).fetchall()
    if not rows:
        raise SystemExit(f"No rows returned for: {where_sql}")

    offset = 5 if include_meta else 0
    meta_rows = [row[:offset] for row in rows] if include_meta else None
    data = np.asarray([row[offset:] for row in rows], dtype=np.float64)
    return meta_rows, data[:, :-1], data[:, -1]


def standardize_train(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std < 1e-8] = 1.0
    return (x - mean) / std, mean, std


def apply_standardize(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return (x - mean) / std


def fit_ridge(x: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    x_design = np.column_stack([np.ones(len(x)), x])
    penalty = np.eye(x_design.shape[1]) * alpha
    penalty[0, 0] = 0.0
    return np.linalg.solve(x_design.T @ x_design + penalty, x_design.T @ y)


def predict(x: np.ndarray, coef: np.ndarray) -> np.ndarray:
    x_design = np.column_stack([np.ones(len(x)), x])
    return np.maximum(x_design @ coef, 0.0)


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    err = y_pred - y_true
    denom = np.abs(y_true) + np.abs(y_pred)
    smape_terms = np.zeros_like(denom, dtype=np.float64)
    mask = denom > 0
    smape_terms[mask] = 2 * np.abs(err[mask]) / denom[mask]
    ss_res = float(np.sum(err**2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    return {
        "mae": round(float(np.mean(np.abs(err))), 6),
        "rmse": round(float(np.sqrt(np.mean(err**2))), 6),
        "smape": round(float(np.mean(smape_terms)), 6),
        "r2": round(1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0, 6),
    }


def topk_overlap(meta_rows: Iterable[tuple], y_true: np.ndarray, y_pred: np.ndarray, k: int = 5) -> float:
    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for meta, actual, pred in zip(meta_rows, y_true, y_pred, strict=True):
        grouped[str(meta[1])].append((float(actual), float(pred)))

    overlaps: list[float] = []
    for rows in grouped.values():
        if len(rows) < k:
            continue
        actual_top = {
            index
            for index, _ in sorted(enumerate(rows), key=lambda item: item[1][0], reverse=True)[:k]
        }
        pred_top = {
            index
            for index, _ in sorted(enumerate(rows), key=lambda item: item[1][1], reverse=True)[:k]
        }
        overlaps.append(len(actual_top & pred_top) / k)
    return round(float(np.mean(overlaps)), 6) if overlaps else 0.0


def write_prediction_sample(meta_rows: list[tuple], y_true: np.ndarray, y_pred: np.ndarray) -> None:
    PREDICTION_SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ranked = sorted(
        zip(meta_rows, y_true, y_pred, strict=True),
        key=lambda row: abs(float(row[1]) - float(row[2])),
        reverse=True,
    )[:300]
    with PREDICTION_SAMPLE_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "pickup_5min",
                "target_5min",
                "pickup_location_id",
                "zone",
                "zone_type",
                "actual_t_plus_5",
                "predicted_t_plus_5",
                "absolute_error",
            ],
        )
        writer.writeheader()
        for meta, actual, pred in ranked:
            writer.writerow(
                {
                    "pickup_5min": meta[0],
                    "target_5min": meta[1],
                    "pickup_location_id": meta[2],
                    "zone": meta[3],
                    "zone_type": meta[4],
                    "actual_t_plus_5": round(float(actual), 4),
                    "predicted_t_plus_5": round(float(pred), 4),
                    "absolute_error": round(abs(float(actual) - float(pred)), 4),
                }
            )


def coefficient_table(coef: np.ndarray, feature_names: list[str]) -> list[dict[str, object]]:
    rows = [
        {"feature": name, "standardized_coefficient": round(float(value), 8)}
        for name, value in zip(feature_names, coef[1:], strict=True)
    ]
    return sorted(rows, key=lambda row: abs(float(row["standardized_coefficient"])), reverse=True)


def write_report(payload: dict[str, object]) -> None:
    context_metrics = payload["metrics"]["context_ridge_model"]
    baseline_metrics = payload["comparison"]["baseline_ridge_model"]
    delta = payload["comparison"]["delta_context_minus_baseline"]
    top_context_features = [
        row
        for row in payload["model"]["top_standardized_coefficients"]
        if row["feature"]
        in {
            "temperature_2m_c",
            "precipitation_mm",
            "wind_speed_10m_kmh",
            "is_rain",
            "subway_ridership",
            "subway_transfers",
            "log_subway_ridership",
            "is_us_federal_holiday",
            "is_day_before_holiday",
            "is_day_after_holiday",
        }
    ][:8]
    lines = [
        "# NYC Context-Aware Demand Model",
        "",
        "This model joins real NYC taxi pickup labels with weather, US holiday,",
        "and Manhattan subway ridership features.",
        "",
        "## Metrics",
        "",
        "| Model | MAE | RMSE | sMAPE | R2 | Top-5 overlap |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| Context Ridge | {context_metrics['mae']} | {context_metrics['rmse']} | "
            f"{context_metrics['smape']} | {context_metrics['r2']} | "
            f"{payload['top5_overlap']['context_ridge_model']} |"
        ),
        (
            f"| Previous Ridge baseline | {baseline_metrics['mae']} | {baseline_metrics['rmse']} | "
            f"{baseline_metrics['smape']} | {baseline_metrics['r2']} | "
            f"{payload['comparison']['baseline_top5_overlap']} |"
        ),
        "",
        "## Delta",
        "",
        f"- MAE delta: `{delta['mae']}`",
        f"- RMSE delta: `{delta['rmse']}`",
        f"- sMAPE delta: `{delta['smape']}`",
        f"- R2 delta: `{delta['r2']}`",
        f"- Top-5 overlap delta: `{payload['comparison']['delta_top5_overlap']}`",
        "",
        "## Context Feature Coefficients",
        "",
        "| Feature | Standardized coefficient |",
        "|---|---:|",
    ]
    for row in top_context_features:
        lines.append(f"| {row['feature']} | {row['standardized_coefficient']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Recent taxi demand remains the strongest short-horizon predictor. Context",
            "features provide explainability and scenario signals, but they may only",
            "modestly improve a 5-minute horizon because the lagged taxi signal is already",
            "very strong.",
            "",
            "Subway ridership is the strongest added context feature by standardized",
            "coefficient, while weather and holiday signals are weaker at the 5-minute",
            "horizon. This is still useful for the A-Eye story: public mobility pressure can",
            "be joined to real taxi labels, but exact Gangnam taxi labels are required before",
            "claiming exact Gangnam taxi counts.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def train(args: argparse.Namespace) -> dict[str, object]:
    if not NYC_CONTEXT_PARQUET.exists():
        raise SystemExit("Missing enriched context parquet. Run build_nyc_context_features.py first.")
    baseline_payload = json.loads(BASELINE_METRIC_PATH.read_text(encoding="utf-8"))

    con = duckdb.connect()
    con.execute("set threads to 4")
    train_where = f"""
      pickup_5min < cast({sql_literal(args.test_month + '-01')} as timestamp)
      and target_pickup_count_t_plus_5 is not null
      and hash(cast(pickup_5min as varchar) || '-' || cast(pickup_location_id as varchar)) % 1000
        < {args.sample_per_mille}
    """
    test_where = f"""
      pickup_5min >= cast({sql_literal(args.test_month + '-01')} as timestamp)
      and pickup_5min < cast({sql_literal(args.test_month + '-01')} as timestamp) + interval 1 month
      and target_pickup_count_t_plus_5 is not null
    """
    _, x_train, y_train = load_matrix(con, train_where, args.max_train_rows)
    test_meta, x_test, y_test = load_matrix(con, test_where, None, include_meta=True)
    con.close()

    x_train_std, mean, std = standardize_train(x_train)
    x_test_std = apply_standardize(x_test, mean, std)
    coef = fit_ridge(x_train_std, y_train, args.alpha)
    pred = predict(x_test_std, coef)

    model_metrics = metrics(y_test, pred)
    model_top5 = topk_overlap(test_meta or [], y_test, pred)
    baseline_metrics = baseline_payload["metrics"]["ridge_model"]
    baseline_top5 = baseline_payload["top5_overlap"]["ridge_model"]
    feature_names = [name for name, _ in FEATURE_EXPRESSIONS]
    coefficients = coefficient_table(coef, feature_names)

    payload = {
        "source": "NYC TLC + Open-Meteo + MTA Subway Hourly Ridership + US holidays",
        "training_table": str(NYC_CONTEXT_PARQUET.relative_to(WORKSPACE_DIR)),
        "target": "target_pickup_count_t_plus_5",
        "split": {
            "train": f"2025-01 through month before {args.test_month}",
            "test": args.test_month,
        },
        "row_counts": {
            "train_sample": int(len(y_train)),
            "test": int(len(y_test)),
        },
        "model": {
            "type": "context_ridge_regression",
            "alpha": args.alpha,
            "features": feature_names,
            "intercept": float(coef[0]),
            "coefficients": [float(value) for value in coef[1:]],
            "feature_mean": [float(value) for value in mean],
            "feature_std": [float(value) for value in std],
            "top_standardized_coefficients": coefficients[:20],
        },
        "metrics": {
            "context_ridge_model": model_metrics,
        },
        "top5_overlap": {
            "context_ridge_model": model_top5,
        },
        "comparison": {
            "baseline_ridge_model": baseline_metrics,
            "baseline_top5_overlap": baseline_top5,
            "delta_context_minus_baseline": {
                key: round(model_metrics[key] - baseline_metrics[key], 6)
                for key in ["mae", "rmse", "smape", "r2"]
            },
            "delta_top5_overlap": round(model_top5 - baseline_top5, 6),
        },
        "notes": [
            "Context features are joined by local NYC hour.",
            "Subway ridership is Manhattan-wide hourly pressure, not station-to-zone exact matching.",
            "Gangnam still needs exact taxi labels for exact count prediction.",
        ],
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(payload["model"], ensure_ascii=False, indent=2), encoding="utf-8")
    METRIC_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_prediction_sample(test_meta or [], y_test, pred)
    write_report(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-month", default="2026-03")
    parser.add_argument("--sample-per-mille", type=int, default=180)
    parser.add_argument("--max-train-rows", type=int, default=1_500_000)
    parser.add_argument("--alpha", type=float, default=25.0)
    args = parser.parse_args()
    payload = train(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"saved model: {MODEL_PATH}")
    print(f"saved metrics: {METRIC_PATH}")
    print(f"saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()

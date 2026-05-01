from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
NYC_TRANSFER_DIR = WORKSPACE_DIR / "a-eye-us-taxi-transfer"
NYC_PYTHON_PACKAGES = NYC_TRANSFER_DIR / ".python-packages"
NYC_TRAINING_PARQUET = (
    NYC_TRANSFER_DIR
    / "processed"
    / "nyc_yellow_2025_01_2026_03_manhattan_5min_training_tplus5.parquet"
)
MODEL_DIR = ROOT_DIR / "models"
MODEL_PATH = MODEL_DIR / "nyc_baseline_ridge_model.json"
METRIC_DIR = ROOT_DIR / "data" / "processed" / "model"
METRIC_PATH = METRIC_DIR / "nyc_baseline_metrics.json"
PREDICTION_SAMPLE_PATH = METRIC_DIR / "nyc_baseline_prediction_sample.csv"
REPORT_PATH = ROOT_DIR / "docs" / "NYC_BASELINE_MODEL.md"

if NYC_PYTHON_PACKAGES.exists():
    sys.path.insert(0, str(NYC_PYTHON_PACKAGES))

try:
    import duckdb
except ImportError as exc:
    raise SystemExit(
        "duckdb is required. Run the NYC collection setup first, or install "
        "duckdb into ../a-eye-us-taxi-transfer/.python-packages."
    ) from exc


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
        from read_parquet({sql_literal(NYC_TRAINING_PARQUET)})
        where {where_sql}
        {limit_sql}
        """
    ).fetchall()
    if not rows:
        raise SystemExit(f"No rows returned for: {where_sql}")

    meta_rows = None
    offset = 5 if include_meta else 0
    if include_meta:
        meta_rows = [row[:offset] for row in rows]
    data = np.asarray([row[offset:] for row in rows], dtype=np.float64)
    x = data[:, :-1]
    y = data[:, -1]
    return meta_rows, x, y


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
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    denom = np.abs(y_true) + np.abs(y_pred)
    smape_terms = np.zeros_like(denom, dtype=np.float64)
    mask = denom > 0
    smape_terms[mask] = 2 * np.abs(err[mask]) / denom[mask]
    smape = float(np.mean(smape_terms))
    ss_res = float(np.sum(err**2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "smape": round(smape, 6),
        "r2": round(r2, 6),
    }


def topk_overlap(
    meta_rows: Iterable[tuple],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    k: int = 5,
) -> float:
    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for meta, actual, pred in zip(meta_rows, y_true, y_pred, strict=True):
        target_5min = str(meta[1])
        grouped[target_5min].append((float(actual), float(pred)))

    overlaps: list[float] = []
    for rows in grouped.values():
        if len(rows) < k:
            continue
        actual_top = {
            index
            for index, _ in sorted(
                enumerate(rows),
                key=lambda item: item[1][0],
                reverse=True,
            )[:k]
        }
        pred_top = {
            index
            for index, _ in sorted(
                enumerate(rows),
                key=lambda item: item[1][1],
                reverse=True,
            )[:k]
        }
        overlaps.append(len(actual_top & pred_top) / k)
    return round(float(np.mean(overlaps)), 6) if overlaps else 0.0


def write_prediction_sample(
    meta_rows: list[tuple],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    path: Path,
    limit: int = 300,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ranked = sorted(
        zip(meta_rows, y_true, y_pred, strict=True),
        key=lambda row: abs(float(row[1]) - float(row[2])),
        reverse=True,
    )[:limit]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
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


def write_report(payload: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    model_metrics = payload["metrics"]["ridge_model"]
    persistence_metrics = payload["metrics"]["persistence_baseline"]
    rolling_metrics = payload["metrics"]["rolling_1h_baseline"]
    lines = [
        "# NYC Baseline Demand Model",
        "",
        "This is the first trainable baseline for the A-Eye demand project.",
        "It uses real NYC TLC 5-minute taxi pickup labels to predict taxi demand",
        "`t+5min` at the Manhattan taxi-zone level.",
        "",
        "## Split",
        "",
        f"- Train: `{payload['split']['train']}`",
        f"- Test: `{payload['split']['test']}`",
        f"- Training sample rows: `{payload['row_counts']['train_sample']:,}`",
        f"- Test rows: `{payload['row_counts']['test']:,}`",
        "",
        "## Metrics",
        "",
        "| Model | MAE | RMSE | sMAPE | R2 | Top-5 overlap |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| Ridge baseline | {model_metrics['mae']} | {model_metrics['rmse']} | "
            f"{model_metrics['smape']} | {model_metrics['r2']} | "
            f"{payload['top5_overlap']['ridge_model']} |"
        ),
        (
            f"| Persistence baseline | {persistence_metrics['mae']} | "
            f"{persistence_metrics['rmse']} | {persistence_metrics['smape']} | "
            f"{persistence_metrics['r2']} | {payload['top5_overlap']['persistence_baseline']} |"
        ),
        (
            f"| Rolling 1h baseline | {rolling_metrics['mae']} | "
            f"{rolling_metrics['rmse']} | {rolling_metrics['smape']} | "
            f"{rolling_metrics['r2']} | {payload['top5_overlap']['rolling_1h_baseline']} |"
        ),
        "",
        "## Use In A-Eye",
        "",
        "This proves the project can train and evaluate a real `t -> t+5min`",
        "taxi-demand model when exact pickup labels exist. Gangnam still remains",
        "a relative heatmap dry test because exact Kakao Taxi pickup labels are not",
        "available in the public dataset.",
        "",
        "## Outputs",
        "",
        f"- `{MODEL_PATH.relative_to(ROOT_DIR)}`",
        f"- `{METRIC_PATH.relative_to(ROOT_DIR)}`",
        f"- `{PREDICTION_SAMPLE_PATH.relative_to(ROOT_DIR)}`",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def train(args: argparse.Namespace) -> dict[str, object]:
    if not NYC_TRAINING_PARQUET.exists():
        raise SystemExit(f"Missing NYC training parquet: {NYC_TRAINING_PARQUET}")

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

    x_train_std, mean, std = standardize_train(x_train)
    x_test_std = apply_standardize(x_test, mean, std)
    coef = fit_ridge(x_train_std, y_train, args.alpha)

    pred_model = predict(x_test_std, coef)
    pred_persistence = np.maximum(x_test[:, 0], 0.0)
    pred_rolling = np.maximum(x_test[:, 4], 0.0)

    payload = {
        "source": "NYC TLC Yellow Taxi Trip Records",
        "training_table": str(NYC_TRAINING_PARQUET.relative_to(WORKSPACE_DIR)),
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
            "type": "ridge_regression",
            "alpha": args.alpha,
            "features": [name for name, _ in FEATURE_EXPRESSIONS],
            "intercept": float(coef[0]),
            "coefficients": [float(value) for value in coef[1:]],
            "feature_mean": [float(value) for value in mean],
            "feature_std": [float(value) for value in std],
        },
        "metrics": {
            "ridge_model": metrics(y_test, pred_model),
            "persistence_baseline": metrics(y_test, pred_persistence),
            "rolling_1h_baseline": metrics(y_test, pred_rolling),
        },
        "top5_overlap": {
            "ridge_model": topk_overlap(test_meta or [], y_test, pred_model, k=5),
            "persistence_baseline": topk_overlap(test_meta or [], y_test, pred_persistence, k=5),
            "rolling_1h_baseline": topk_overlap(test_meta or [], y_test, pred_rolling, k=5),
        },
        "notes": [
            "This model is trained on real NYC 5-minute taxi pickup labels.",
            "Use it as a baseline and proof of the t+5min learning structure.",
            "Do not claim exact Gangnam taxi counts without Gangnam taxi labels.",
        ],
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(payload["model"], ensure_ascii=False, indent=2), encoding="utf-8")
    METRIC_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_prediction_sample(test_meta or [], y_test, pred_model, PREDICTION_SAMPLE_PATH)
    write_report(payload)
    con.close()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-month", default="2026-03")
    parser.add_argument("--sample-per-mille", type=int, default=180)
    parser.add_argument("--max-train-rows", type=int, default=1_500_000)
    parser.add_argument("--alpha", type=float, default=25.0)
    args = parser.parse_args()
    if not 1 <= args.sample_per_mille <= 1000:
        raise SystemExit("--sample-per-mille must be between 1 and 1000")

    payload = train(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"saved model: {MODEL_PATH}")
    print(f"saved metrics: {METRIC_PATH}")
    print(f"saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config


ZONE_COORDS = {
    "A1": (0, 0),
    "A2": (0, 1),
    "A3": (0, 2),
    "B1": (1, 0),
    "B2": (1, 1),
    "B3": (1, 2),
    "C1": (2, 0),
    "C2": (2, 1),
    "C3": (2, 2),
}

MARKET_CRUISE_PRIOR = {
    "A1": 0.85,
    "A2": 1.15,
    "A3": 1.05,
    "B1": 0.95,
    "B2": 1.45,
    "B3": 1.25,
    "C1": 0.70,
    "C2": 1.20,
    "C3": 0.80,
}

HOTSPOT_PRIORITY = {
    "A1": 0.05,
    "A2": 0.32,
    "A3": 0.12,
    "B1": 0.08,
    "B2": 0.55,
    "B3": 0.26,
    "C1": 0.02,
    "C2": 0.30,
    "C3": 0.07,
}


def allocate_supply_by_demand(demand: pd.Series, total_supply: int) -> pd.Series:
    if total_supply <= 0 or demand.sum() <= 0:
        return pd.Series([0] * len(demand), index=demand.index, dtype=int)

    weights = demand / demand.sum()
    raw = weights * total_supply
    allocated = raw.astype(int)
    remainder = int(total_supply - allocated.sum())

    if remainder > 0:
        order = (raw - allocated).sort_values(ascending=False).index.tolist()
        for idx in order[:remainder]:
            allocated.loc[idx] += 1

    return allocated.astype(int)


def allocate_from_scores(scores: pd.Series, total_supply: int) -> pd.Series:
    if len(scores) <= 0 or total_supply <= 0 or scores.sum() <= 0:
        return pd.Series([0] * len(scores), index=scores.index, dtype=int)

    weights = scores / scores.sum()
    raw = weights * total_supply
    allocated = raw.astype(int)
    remainder = int(total_supply - allocated.sum())

    if remainder > 0:
        order = (raw - allocated).sort_values(ascending=False).index.tolist()
        for idx in order[:remainder]:
            allocated.loc[idx] += 1

    return allocated.astype(int)


def manhattan_distance(zone_a: str, zone_b: str) -> int:
    ax, ay = ZONE_COORDS[zone_a]
    bx, by = ZONE_COORDS[zone_b]
    return abs(ax - bx) + abs(ay - by)


def allocate_market_cruise_supply(df: pd.DataFrame, total_supply: int, zone_col: str) -> pd.Series:
    scores = df[zone_col].map(MARKET_CRUISE_PRIOR).astype(float)
    return allocate_from_scores(scores, total_supply)


def allocate_kakao_like_supply(df: pd.DataFrame, total_supply: int, zone_col: str, demand_col: str) -> pd.Series:
    demand_share = df[demand_col] / max(float(df[demand_col].sum()), 1.0)
    hotspot_score = df[zone_col].map(HOTSPOT_PRIORITY).astype(float)
    proximity_score = df[zone_col].map(lambda zone: 1.0 / (1.0 + manhattan_distance(zone, "B2"))).astype(float)
    corridor_bonus = df[zone_col].map(lambda zone: 0.12 if zone in {"A2", "B2", "C2", "B3"} else 0.0).astype(float)

    score = (
        demand_share * 0.58
        + hotspot_score * 0.22
        + proximity_score * 0.12
        + corridor_bonus * 0.08
    )
    score = score.clip(lower=0.001)
    return allocate_from_scores(score, total_supply)


def allocation_label() -> str:
    return "compare market-cruise allocation against kakao-like heuristic reallocation"


def summarize_metrics(df: pd.DataFrame, supply_col: str, demand_col: str) -> dict[str, float | int]:
    shortage = (df[demand_col] - df[supply_col]).clip(lower=0)
    abs_gap = (df[demand_col] - df[supply_col]).abs()
    return {
        "total_supply": int(df[supply_col].sum()),
        "total_dispatch_demand": round(float(df[demand_col].sum()), 4),
        "total_shortage": round(float(shortage.sum()), 4),
        "mean_abs_gap": round(float(abs_gap.mean()), 4),
        "zones_with_shortage": int((shortage > 0).sum()),
        "max_shortage": round(float(shortage.max()), 4),
    }


def plot_comparison(summary: dict, output_path: Path) -> None:
    before = summary["before"]
    after = summary["after"]
    labels = ["Total shortage", "Mean abs gap", "Zones with shortage"]
    before_values = [
        before["total_shortage"],
        before["mean_abs_gap"],
        before["zones_with_shortage"],
    ]
    after_values = [
        after["total_shortage"],
        after["mean_abs_gap"],
        after["zones_with_shortage"],
    ]

    plt.figure(figsize=(10, 5))
    x = range(len(labels))
    width = 0.35
    plt.bar([i - width / 2 for i in x], before_values, width=width, label="Before")
    plt.bar([i + width / 2 for i in x], after_values, width=width, label="After")
    plt.xticks(list(x), labels)
    plt.ylabel("Value")
    plt.title("Dispatch Before vs After Reallocation")
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def main() -> None:
    cfg = load_config()
    dispatch_csv = Path(cfg["dispatch"]["output_csv"])
    comparison_output = Path(cfg["analysis"]["dispatch_comparison_output"])
    eval_output = Path(cfg["analysis"]["dispatch_eval_output"])
    plot_output = Path(cfg["visualization"]["dispatch_eval_plot_output"])

    df = pd.read_csv(dispatch_csv).copy()
    if df.empty:
        raise SystemExit("Dispatch output is empty. Run the dispatch step first.")

    before_supply_col = "available_taxis"
    baseline_supply_col = "baseline_before_taxis"
    demand_col = "dispatch_demand"
    after_supply_col = "reallocated_taxis"
    zone_col = cfg["data"]["zone_column"]

    total_supply = int(df[before_supply_col].sum())
    df[baseline_supply_col] = allocate_market_cruise_supply(df, total_supply, zone_col)
    df[after_supply_col] = allocate_kakao_like_supply(df, total_supply, zone_col, demand_col)

    df["current_shortage"] = (df[demand_col] - df[before_supply_col]).clip(lower=0)
    df["before_shortage"] = (df[demand_col] - df[baseline_supply_col]).clip(lower=0)
    df["after_shortage"] = (df[demand_col] - df[after_supply_col]).clip(lower=0)
    df["current_abs_gap"] = (df[demand_col] - df[before_supply_col]).abs()
    df["before_abs_gap"] = (df[demand_col] - df[baseline_supply_col]).abs()
    df["after_abs_gap"] = (df[demand_col] - df[after_supply_col]).abs()
    df["current_imbalance_score"] = df["imbalance_score"]
    df["before_imbalance_score"] = df.apply(
        lambda row: row[demand_col] / max(row[baseline_supply_col], 1),
        axis=1,
    )
    df["after_imbalance_score"] = df.apply(
        lambda row: row[demand_col] / max(row[after_supply_col], 1),
        axis=1,
    )
    df["taxis_moved"] = df[after_supply_col] - df[before_supply_col]

    summary = {
        "timestamp": str(df["pickup_datetime"].iloc[0]),
        "strategy": allocation_label(),
        "current_reference": summarize_metrics(df, before_supply_col, demand_col),
        "before": summarize_metrics(df, baseline_supply_col, demand_col),
        "after": summarize_metrics(df, after_supply_col, demand_col),
    }

    comparison_output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(comparison_output, index=False)
    eval_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    plot_comparison(summary, plot_output)

    print(f"saved: {comparison_output}")
    print(f"saved: {eval_output}")
    print(f"saved: {plot_output}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

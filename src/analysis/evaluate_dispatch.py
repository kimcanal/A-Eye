from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config


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


def allocate_uniform_supply(count: int, total_supply: int, index: pd.Index) -> pd.Series:
    if count <= 0 or total_supply <= 0:
        return pd.Series([0] * count, index=index, dtype=int)

    base = total_supply // count
    remainder = total_supply % count
    values = [base] * count
    for i in range(remainder):
        values[i] += 1
    return pd.Series(values, index=index, dtype=int)


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

    total_supply = int(df[before_supply_col].sum())
    df[baseline_supply_col] = allocate_uniform_supply(len(df), total_supply, df.index)
    df[after_supply_col] = allocate_supply_by_demand(df[demand_col], total_supply)

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
        "strategy": "compare uniform baseline allocation against predicted-demand reallocation",
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

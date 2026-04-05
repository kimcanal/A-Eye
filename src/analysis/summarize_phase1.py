from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_config


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg["data"]["processed_csv"])
    zone_output = Path(cfg["analysis"]["zone_summary_output"])
    hour_output = Path(cfg["analysis"]["hour_summary_output"])
    demand_column = cfg["data"]["demand_column"]
    zone_column = cfg["data"]["zone_column"]
    supply_column = cfg["data"]["supply_column"]

    df = pd.read_csv(processed_csv)
    metadata_columns = [
        c
        for c in ["zone_name", "gu_name", "city_name", "full_zone_name"]
        if c in df.columns
    ]

    zone_agg = {
        demand_column: ["sum", "mean"],
        supply_column: "mean",
    }
    for col in metadata_columns:
        zone_agg[col] = "first"

    zone_summary = (
        df.groupby(zone_column, as_index=False)
        .agg(zone_agg)
    )
    zone_summary.columns = [
        "_".join([part for part in col if part]).rstrip("_")
        if isinstance(col, tuple)
        else col
        for col in zone_summary.columns.to_flat_index()
    ]
    rename_map = {
        f"{demand_column}_sum": "total_demand",
        f"{demand_column}_mean": "avg_demand",
        f"{supply_column}_mean": "avg_supply",
    }
    for col in metadata_columns:
        rename_map[f"{col}_first"] = col
    zone_summary = zone_summary.rename(columns=rename_map)
    zone_summary = zone_summary.sort_values("total_demand", ascending=False)
    zone_summary["avg_imbalance"] = zone_summary["avg_demand"] / zone_summary["avg_supply"].clip(lower=1)
    ordered_zone_columns = [
        zone_column,
        *[c for c in ["full_zone_name", "gu_name", "zone_name", "city_name"] if c in zone_summary.columns],
        "total_demand",
        "avg_demand",
        "avg_supply",
        "avg_imbalance",
    ]
    zone_summary = zone_summary[ordered_zone_columns]

    hour_summary = (
        df.groupby("hour", as_index=False)
        .agg(total_demand=(demand_column, "sum"), avg_demand=(demand_column, "mean"))
        .sort_values("hour")
    )

    zone_output.parent.mkdir(parents=True, exist_ok=True)
    zone_summary.to_csv(zone_output, index=False)
    hour_summary.to_csv(hour_output, index=False)

    print(f"saved: {zone_output}")
    print(f"saved: {hour_output}")


if __name__ == "__main__":
    main()

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

    zone_summary = (
        df.groupby(zone_column, as_index=False)
        .agg(
            total_demand=(demand_column, "sum"),
            avg_demand=(demand_column, "mean"),
            avg_supply=(supply_column, "mean"),
        )
        .sort_values("total_demand", ascending=False)
    )
    zone_summary["avg_imbalance"] = zone_summary["avg_demand"] / zone_summary["avg_supply"].clip(lower=1)

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

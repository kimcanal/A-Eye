from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_config


def compute_imbalance_score(demand: float, supply: float) -> float:
    return demand / max(supply, 1)


def incentive_multiplier(score: float, low: float, medium: float, high: float) -> float:
    if score < low:
        return 1.0
    if score < medium:
        return 1.1
    if score < high:
        return 1.25
    return 1.5


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg['data']['processed_csv'])
    output_csv = Path(cfg['dispatch']['output_csv'])
    time_column = cfg['data']['time_column']
    demand_column = cfg['data']['demand_column']
    supply_column = cfg['data']['supply_column']
    zone_column = cfg['data']['zone_column']

    df = pd.read_csv(processed_csv).copy()
    df[time_column] = pd.to_datetime(df[time_column])
    latest = df.sort_values(time_column).groupby(zone_column, as_index=False).tail(1).copy()

    latest['imbalance_score'] = latest.apply(
        lambda row: compute_imbalance_score(row[demand_column], row[supply_column]), axis=1
    )
    latest['incentive_multiplier'] = latest['imbalance_score'].apply(
        lambda score: incentive_multiplier(
            score,
            cfg['dispatch']['low_threshold'],
            cfg['dispatch']['medium_threshold'],
            cfg['dispatch']['high_threshold'],
        )
    )

    latest = latest[[time_column, zone_column, demand_column, supply_column, 'imbalance_score', 'incentive_multiplier']].sort_values(
        'imbalance_score', ascending=False
    ).reset_index(drop=True)
    latest.insert(0, 'dispatch_rank', latest.index + 1)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    latest.to_csv(output_csv, index=False)

    print(latest)
    print(f'saved: {output_csv}')


if __name__ == '__main__':
    main()

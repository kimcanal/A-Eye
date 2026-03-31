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


def build_dispatch_frame(cfg: dict) -> pd.DataFrame:
    processed_csv = Path(cfg['data']['processed_csv'])
    predictions_csv = Path(cfg['model']['predictions_output'])
    time_column = cfg['data']['time_column']
    demand_column = cfg['data']['demand_column']
    supply_column = cfg['data']['supply_column']
    zone_column = cfg['data']['zone_column']

    processed = pd.read_csv(processed_csv).copy()
    processed[time_column] = pd.to_datetime(processed[time_column])

    if predictions_csv.exists():
        predictions = pd.read_csv(predictions_csv).copy()
        predictions[time_column] = pd.to_datetime(predictions[time_column])
        latest_prediction_time = predictions[time_column].max()

        latest_predictions = predictions.loc[
            predictions[time_column] == latest_prediction_time,
            [time_column, zone_column, 'actual_call_count', 'predicted_call_count'],
        ].copy()

        latest_processed = processed.loc[
            processed[time_column] == latest_prediction_time,
            [time_column, zone_column, demand_column, supply_column],
        ].copy()

        merged = latest_predictions.merge(
            latest_processed,
            on=[time_column, zone_column],
            how='left',
        )

        if not merged.empty and merged[supply_column].notna().any():
            merged['dispatch_demand'] = merged['predicted_call_count']
            merged['observed_call_count'] = merged['actual_call_count'].fillna(merged[demand_column])
            merged['demand_source'] = 'predicted'
            return merged

    latest = processed.sort_values(time_column).groupby(zone_column, as_index=False).tail(1).copy()
    latest['dispatch_demand'] = latest[demand_column]
    latest['observed_call_count'] = latest[demand_column]
    latest['predicted_call_count'] = latest[demand_column]
    latest['demand_source'] = 'observed'
    return latest


def main() -> None:
    cfg = load_config()
    output_csv = Path(cfg['dispatch']['output_csv'])
    time_column = cfg['data']['time_column']
    supply_column = cfg['data']['supply_column']
    zone_column = cfg['data']['zone_column']

    latest = build_dispatch_frame(cfg)

    latest['imbalance_score'] = latest.apply(
        lambda row: compute_imbalance_score(row['dispatch_demand'], row[supply_column]), axis=1
    )
    latest['incentive_multiplier'] = latest['imbalance_score'].apply(
        lambda score: incentive_multiplier(
            score,
            cfg['dispatch']['low_threshold'],
            cfg['dispatch']['medium_threshold'],
            cfg['dispatch']['high_threshold'],
        )
    )

    latest = latest[
        [
            time_column,
            zone_column,
            'demand_source',
            'observed_call_count',
            'predicted_call_count',
            'dispatch_demand',
            supply_column,
            'imbalance_score',
            'incentive_multiplier',
        ]
    ].sort_values('imbalance_score', ascending=False).reset_index(drop=True)
    latest.insert(0, 'dispatch_rank', latest.index + 1)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    latest.to_csv(output_csv, index=False)

    print(latest)
    print(f'saved: {output_csv}')


if __name__ == '__main__':
    main()

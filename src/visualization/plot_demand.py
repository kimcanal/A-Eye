from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.common.config import load_config


def save_hourly_demand_plot(df: pd.DataFrame, demand_column: str, output: Path) -> None:
    hourly = df.groupby('hour', as_index=False)[demand_column].sum()
    plt.figure(figsize=(8, 4))
    plt.bar(hourly['hour'], hourly[demand_column], color='#4C78A8')
    plt.title('Hourly Demand')
    plt.xlabel('Hour')
    plt.ylabel('Call Count')
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output)
    plt.close()
    print(f'saved: {output}')


def save_zone_heatmap(df: pd.DataFrame, zone_column: str, demand_column: str, output: Path) -> None:
    pivot = df.pivot_table(
        index=zone_column,
        columns='hour',
        values=demand_column,
        aggfunc='mean',
        fill_value=0,
    )
    plt.figure(figsize=(10, 4.5))
    sns.heatmap(pivot, cmap='YlOrRd', linewidths=0.25)
    plt.title('Average Demand by Zone and Hour')
    plt.xlabel('Hour')
    plt.ylabel('Zone')
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output)
    plt.close()
    print(f'saved: {output}')


def save_prediction_plot(predictions_csv: Path, time_column: str, output: Path) -> None:
    if not predictions_csv.exists():
        return

    pred_df = pd.read_csv(predictions_csv)
    if pred_df.empty:
        return

    pred_df[time_column] = pd.to_datetime(pred_df[time_column])
    pred_df = pred_df.sort_values(time_column).reset_index(drop=True)

    plt.figure(figsize=(10, 4.5))
    plt.plot(pred_df[time_column], pred_df['actual_call_count'], label='Actual', linewidth=2)
    plt.plot(pred_df[time_column], pred_df['predicted_call_count'], label='Predicted', linewidth=2)
    plt.title('Actual vs Predicted Demand')
    plt.xlabel('Time')
    plt.ylabel('Call Count')
    plt.legend()
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output)
    plt.close()
    print(f'saved: {output}')


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg['data']['processed_csv'])
    predictions_csv = Path(cfg['model']['predictions_output'])
    df = pd.read_csv(processed_csv)
    save_hourly_demand_plot(df, cfg['data']['demand_column'], Path(cfg['visualization']['hourly_output']))
    save_zone_heatmap(
        df,
        cfg['data']['zone_column'],
        cfg['data']['demand_column'],
        Path(cfg['visualization']['heatmap_output']),
    )
    save_prediction_plot(
        predictions_csv,
        cfg['data']['time_column'],
        Path(cfg['visualization']['prediction_plot_output']),
    )


if __name__ == '__main__':
    main()

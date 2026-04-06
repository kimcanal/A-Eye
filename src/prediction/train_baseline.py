from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error

from src.common.config import load_config


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg['data']['processed_csv'])
    time_column = cfg['data']['time_column']
    zone_column = cfg['data']['zone_column']
    demand_column = cfg['data']['demand_column']
    supply_column = cfg['data']['supply_column']
    test_size = cfg['model']['test_size']
    random_state = cfg['model']['random_state']
    n_estimators = cfg['model']['n_estimators']
    metrics_output = Path(cfg['model']['metrics_output'])
    predictions_output = Path(cfg['model']['predictions_output'])

    df = pd.read_csv(processed_csv).dropna().copy()
    if len(df) < 2:
        raise SystemExit('Need at least 2 rows after preprocessing to train the baseline model.')

    df[time_column] = pd.to_datetime(df[time_column])
    df = df.sort_values(time_column).reset_index(drop=True)

    excluded = {
        demand_column,
        time_column,
        zone_column,
        supply_column,
        'source_total_passengers',
    }
    metadata_columns = [
        c
        for c in ["zone_name", "gu_name", "city_name", "full_zone_name"]
        if c in df.columns
    ]
    features = [
        c
        for c in df.columns
        if c not in excluded and c not in metadata_columns and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not features:
        raise SystemExit('No feature columns were found for baseline training.')

    split_idx = max(1, int(len(df) * (1 - test_size)))
    split_idx = min(split_idx, len(df) - 1)

    x_train = df.loc[: split_idx - 1, features]
    y_train = df.loc[: split_idx - 1, demand_column]
    x_test = df.loc[split_idx:, features]
    y_test = df.loc[split_idx:, demand_column]
    meta_test = df.loc[split_idx:, [time_column, zone_column, *metadata_columns]].copy()

    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    model.fit(x_train, y_train)
    pred = model.predict(x_test)

    mse = mean_squared_error(y_test, pred)
    rmse = round(mse ** 0.5, 4)
    mae = round(mean_absolute_error(y_test, pred), 4)
    nonzero_mask = y_test.abs() >= 1e-6
    if nonzero_mask.any():
        mape = round(mean_absolute_percentage_error(y_test[nonzero_mask], pred[nonzero_mask]) * 100, 4)
    else:
        mape = None

    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.write_text(
        json.dumps(
            {
                'model': cfg['model']['name'],
                'rows': int(len(df)),
                'train_rows': int(len(x_train)),
                'test_rows': int(len(x_test)),
                'features': features,
                'rmse': rmse,
                'mae': mae,
                'mape': mape,
            },
            indent=2,
        ),
        encoding='utf-8',
    )

    predictions = meta_test.copy()
    predictions['actual_call_count'] = y_test.to_numpy()
    predictions['predicted_call_count'] = pred
    predictions.to_csv(predictions_output, index=False)

    print('rmse:', rmse)
    print('mae:', mae)
    print('mape:', mape, '%')
    print(f'saved: {metrics_output}')
    print(f'saved: {predictions_output}')


if __name__ == '__main__':
    main()

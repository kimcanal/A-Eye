from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from src.common.config import load_config


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg['data']['processed_csv'])
    demand_column = cfg['data']['demand_column']
    test_size = cfg['model']['test_size']
    random_state = cfg['model']['random_state']

    df = pd.read_csv(processed_csv).dropna().copy()
    excluded = {demand_column, 'pickup_datetime', cfg['data']['zone_column']}
    features = [c for c in df.columns if c not in excluded]

    x_train, x_test, y_train, y_test = train_test_split(
        df[features],
        df[demand_column],
        test_size=test_size,
        random_state=random_state,
    )

    model = RandomForestRegressor(n_estimators=200, random_state=random_state)
    model.fit(x_train, y_train)
    pred = model.predict(x_test)

    mse = mean_squared_error(y_test, pred)
    print('rmse:', round(mse ** 0.5, 4))
    print('mae:', round(mean_absolute_error(y_test, pred), 4))


if __name__ == '__main__':
    main()

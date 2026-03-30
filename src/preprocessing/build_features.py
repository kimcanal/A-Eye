from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_config


def add_time_features(
    df: pd.DataFrame,
    time_column: str,
    use_hour: bool,
    use_day_of_week: bool,
) -> pd.DataFrame:
    out = df.copy()
    out[time_column] = pd.to_datetime(out[time_column])
    ts = out[time_column]
    if use_hour:
        out['hour'] = ts.dt.hour
    if use_day_of_week:
        out['day_of_week'] = ts.dt.dayofweek
    return out


def add_demand_features(
    df: pd.DataFrame,
    zone_column: str,
    demand_column: str,
    time_column: str,
    use_lag_1: bool,
    use_rolling_mean_3: bool,
) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values([zone_column, time_column]).reset_index(drop=True)
    if use_lag_1:
        out['lag_1'] = out.groupby(zone_column)[demand_column].shift(1)
    if use_rolling_mean_3:
        out['rolling_mean_3'] = out.groupby(zone_column)[demand_column].transform(
            lambda s: s.rolling(3, min_periods=1).mean()
        )
    return out


def main() -> None:
    cfg = load_config()
    input_csv = Path(cfg['data']['input_csv'])
    output_csv = Path(cfg['data']['processed_csv'])
    time_column = cfg['data']['time_column']
    zone_column = cfg['data']['zone_column']
    demand_column = cfg['data']['demand_column']

    df = pd.read_csv(input_csv)
    df = add_time_features(
        df,
        time_column=time_column,
        use_hour=cfg['features']['use_hour'],
        use_day_of_week=cfg['features']['use_day_of_week'],
    )
    df = add_demand_features(
        df,
        zone_column=zone_column,
        demand_column=demand_column,
        time_column=time_column,
        use_lag_1=cfg['features']['use_lag_1'],
        use_rolling_mean_3=cfg['features']['use_rolling_mean_3'],
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f'saved: {output_csv}')


if __name__ == '__main__':
    main()

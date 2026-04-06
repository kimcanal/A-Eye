from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np
import holidays

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
        # Use only prior observations so the feature remains valid at inference time.
        out['rolling_mean_3'] = out.groupby(zone_column)[demand_column].transform(
            lambda s: s.shift(1).rolling(3, min_periods=1).mean()
        )
    return out


def add_holiday_features(
    df: pd.DataFrame,
    time_column: str,
    use_holiday: bool,
) -> pd.DataFrame:
    out = df.copy()
    if use_holiday:
        kr_holidays = holidays.KR()
        out['is_holiday'] = out[time_column].dt.date.apply(lambda x: int(x in kr_holidays))
    return out


def add_weather_features(
    df: pd.DataFrame,
    time_column: str,
    use_weather: bool,
) -> pd.DataFrame:
    out = df.copy()
    if use_weather:
        # Mock weather data generation using consistent seed based on date
        # Actual implementation would fetch from Meteorological Agency API
        np.random.seed(42)
        dates = out[time_column].dt.date.unique()
        weather_map = {
            date: {
                'temperature': np.random.uniform(-5, 35),
                'precipitation': np.random.choice([0.0, 0.0, 0.0, 5.0, 15.0, 50.0])
            }
            for date in dates
        }
        
        out['temperature'] = out[time_column].dt.date.map(lambda x: weather_map[x]['temperature'])
        out['precipitation'] = out[time_column].dt.date.map(lambda x: weather_map[x]['precipitation'])
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
    df = add_holiday_features(
        df,
        time_column=time_column,
        use_holiday=cfg['features'].get('use_holiday', False),
    )
    df = add_weather_features(
        df,
        time_column=time_column,
        use_weather=cfg['features'].get('use_weather', False),
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f'saved: {output_csv}')


if __name__ == '__main__':
    main()

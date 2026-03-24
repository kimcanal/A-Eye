from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg['data']['processed_csv'])
    df = pd.read_csv(processed_csv)

    hourly = df.groupby('hour', as_index=False)[cfg['data']['demand_column']].sum()
    plt.figure(figsize=(8, 4))
    plt.bar(hourly['hour'], hourly[cfg['data']['demand_column']])
    plt.title('Hourly Demand')
    plt.xlabel('Hour')
    plt.ylabel('Call Count')

    output = Path('outputs/hourly_demand.png')
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output)
    print(f'saved: {output}')


if __name__ == '__main__':
    main()

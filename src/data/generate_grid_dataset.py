from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path

from src.common.config import load_config


def create_3x3_grid_data(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Takes the hotspot data and artificially disaggregates it into a 3x3 grid."""
    
    time_column = cfg['data']['time_column']
    demand_column = cfg['data']['demand_column']
    supply_column = cfg['data']['supply_column']
    
    # Define 3x3 spatial distribution weight matrix (sum = 1.0)
    # Center has highest demand, edges less, corners least.
    weights = np.array([
        [0.05, 0.10, 0.05],
        [0.10, 0.40, 0.10],
        [0.05, 0.10, 0.05]
    ])
    
    grid_records = []
    
    df = df.sort_values(time_column).reset_index(drop=True)
    
    for idx, row in df.iterrows():
        t = row[time_column]
        total_demand = row[demand_column]
        total_supply = row[supply_column]
        
        # Additional features
        is_holiday = row.get('is_holiday', 0)
        temp = row.get('temperature', 15.0)
        precip = row.get('precipitation', 0.0)
        
        # Disaggregate based on weights
        demand_grid = total_demand * weights
        supply_grid = total_supply * weights
        
        for i in range(3):
            for j in range(3):
                grid_records.append({
                    time_column: t,
                    'grid_x': j,
                    'grid_y': i,
                    demand_column: demand_grid[i, j],
                    supply_column: supply_grid[i, j],
                    'is_holiday': is_holiday,
                    'temperature': temp,
                    'precipitation': precip
                })
                
    return pd.DataFrame(grid_records)


def main() -> None:
    cfg = load_config()
    processed_csv = Path(cfg['data']['processed_csv'])
    output_csv = Path(cfg['grid']['output_csv'])
    zone_column = cfg['data']['zone_column']
    demand_column = cfg['data']['demand_column']
    
    print(f"Loading data from {processed_csv}...")
    df = pd.read_csv(processed_csv)
    
    # 1. Find the Hotspot Zone (zone with the maximum total demand)
    zone_totals = df.groupby(zone_column)[demand_column].sum()
    hotspot_zone = zone_totals.idxmax()
    print(f"✅ Hotspot selected: Zone '{hotspot_zone}' (Total Demand: {zone_totals[hotspot_zone]:.2f})")
    
    # 2. Filter for the Hotspot only
    hotspot_df = df[df[zone_column] == hotspot_zone].copy()
    
    # 3. Create synthetic Grid data
    print("Generating 3x3 synthetic grid dataset...")
    grid_df = create_3x3_grid_data(hotspot_df, cfg)
    
    # 4. Save to CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    grid_df.to_csv(output_csv, index=False)
    
    print(f"✅ Grid dataset saved to: {output_csv}")
    print(f"Total sequences (timestamps) generated: {len(hotspot_df)}")
    print(f"Total grid cells generated: {len(grid_df)}")


if __name__ == "__main__":
    main()

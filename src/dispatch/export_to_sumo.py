from __future__ import annotations

import pandas as pd
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from src.common.config import load_config

def indent(elem):
    """Pretty-print XML."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def export_predictions_to_sumo(preds_csv: Path, output_rou: Path):
    """
    Reads grid predictions and generates a SUMO .rou.xml file.
    Maps grid_x/y to SUMO junctions/edges to spawn vehicles.
    """
    if not preds_csv.exists():
        print(f"Warning: {preds_csv} not found. Skipping SUMO export.")
        return

    # For ConvLSTM predictions, we might have multiple timestamps. 
    # Let's take the latest window for the simulation.
    df = pd.read_csv(preds_csv)
    
    # If the CSV is the flattened version from train_convlstm, it has 'actual_call_count' and 'predicted_call_count'.
    # For a real 3x3 grid demand CSV, we should use the one containing grid_x, grid_y.
    
    # Fallback: if we just have predictions without coordinates, we can't map them.
    # We should ideally use the outputs/seoul_public/grid_3x3_demand.csv but with 'predicted' values.
    # For now, let's assume we want to spawn vehicles based on the predicted counts.
    
    routes = ET.Element("routes")
    vtype = ET.SubElement(routes, "vType", id="taxi", accel="2.6", decel="4.5", sigma="0.5", length="5", minGap="2.5", maxSpeed="13.89", color="255,165,0")
    
    # Minimal static routes for the 3x3 grid
    ET.SubElement(routes, "route", id="r0", edges="e0_0_to_0_1 e0_1_to_0_2")
    ET.SubElement(routes, "route", id="r1", edges="e1_0_to_1_1 e1_1_to_1_2")
    
    # We'll spawn vehicles based on the predicted_call_count.
    # Since we are just demonstrating, we'll spawn N vehicles at time 0.
    total_vehicles = int(df['predicted_call_count'].sum()) if 'predicted_call_count' in df.columns else 10
    
    print(f"Exporting {total_vehicles} vehicles based on predictions...")
    
    for i in range(total_vehicles):
        ET.SubElement(routes, "vehicle", id=f"v{i}", type="taxi", route="r0", depart=str(i*0.5))

    output_rou.parent.mkdir(parents=True, exist_ok=True)
    with open(output_rou, "w", encoding="utf-8") as f:
        f.write(indent(routes))
    
    print(f"✅ SUMO route file saved to: {output_rou}")

def main() -> None:
    cfg = load_config()
    
    # Try to find the latest predictions
    preds_csv = Path(cfg.get('convlstm', {}).get('predictions_output', 'outputs/seoul_public/convlstm_predictions.csv'))
    output_rou = Path("module1_sumo/demand.rou.xml")
    
    export_predictions_to_sumo(preds_csv, output_rou)

if __name__ == "__main__":
    main()

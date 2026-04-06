from __future__ import annotations

from pathlib import Path
from xml.dom import minidom
import xml.etree.ElementTree as ET

import pandas as pd

from src.common.config import load_config


ZONE_ROUTE_MAP = {
    "A1": "north_west",
    "A2": "north_center",
    "A3": "north_east",
    "B1": "middle_west",
    "B2": "middle_center",
    "B3": "middle_east",
    "C1": "south_west",
    "C2": "south_center",
    "C3": "south_east",
}

ROUTES = {
    "north_west": "e1_0_to_2_0",
    "north_center": "e1_1_to_2_1",
    "north_east": "e1_2_to_2_2",
    "middle_west": "e1_0_to_1_1",
    "middle_center": "e0_1_to_1_1 e1_1_to_2_1",
    "middle_east": "e0_2_to_1_2",
    "south_west": "e0_0_to_1_0",
    "south_center": "e0_1_to_1_1",
    "south_east": "e0_2_to_1_2",
}


def pretty_xml(root: ET.Element) -> str:
    return minidom.parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(indent="  ")


def build_routes(df: pd.DataFrame, supply_column: str, output_path: Path, label: str) -> None:
    routes = ET.Element("routes")
    ET.SubElement(
        routes,
        "vType",
        id="taxi",
        accel="2.6",
        decel="4.5",
        sigma="0.5",
        length="5",
        minGap="2.5",
        maxSpeed="13.89",
        color="255,165,0",
    )

    for route_id, edges in ROUTES.items():
        ET.SubElement(routes, "route", id=route_id, edges=edges)

    horizon_seconds = 1800.0
    all_departures: list[tuple[str, str, float]] = []
    for _, row in df.iterrows():
        vehicle_count = int(max(0, round(row[supply_column])))
        route_id = ZONE_ROUTE_MAP[row["zone_id"]]
        for i in range(vehicle_count):
            if vehicle_count == 1:
                depart = 0.0
            else:
                depart = (i / max(vehicle_count - 1, 1)) * horizon_seconds
            vehicle_id = f"{label}_{row['zone_id']}_{i:03d}"
            all_departures.append((vehicle_id, route_id, depart))

    all_departures.sort(key=lambda item: item[2])
    for vehicle_id, route_id, depart in all_departures:
        ET.SubElement(routes, "vehicle", id=vehicle_id, type="taxi", route=route_id, depart=f"{depart:.1f}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pretty_xml(routes), encoding="utf-8")
    print(f"saved: {output_path}")


def build_sumocfg(net_file: str, route_file: str, output_path: Path) -> None:
    content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<configuration xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/sumoConfiguration.xsd\">
    <input>
        <net-file value=\"{net_file}\"/>
        <route-files value=\"{route_file}\"/>
    </input>
    <time>
        <begin value=\"0\"/>
        <end value=\"1800\"/>
    </time>
    <report>
        <no-step-log value=\"true\"/>
    </report>
</configuration>
"""
    output_path.write_text(content, encoding="utf-8")
    print(f"saved: {output_path}")


def main() -> None:
    cfg = load_config()
    comparison_csv = Path(cfg["analysis"]["dispatch_comparison_output"])
    if not comparison_csv.exists():
        raise SystemExit(f"Missing dispatch comparison file: {comparison_csv}")

    df = pd.read_csv(comparison_csv).copy()
    before_route_output = Path(cfg["sumo"]["before_route_output"])
    after_route_output = Path(cfg["sumo"]["after_route_output"])
    before_config_output = Path(cfg["sumo"]["before_config_output"])
    after_config_output = Path(cfg["sumo"]["after_config_output"])
    net_file = Path(cfg["sumo"]["net_file"])

    build_routes(df, "baseline_before_taxis", before_route_output, "before")
    build_routes(df, "reallocated_taxis", after_route_output, "after")
    build_sumocfg(net_file.name, before_route_output.name, before_config_output)
    build_sumocfg(net_file.name, after_route_output.name, after_config_output)


if __name__ == "__main__":
    main()

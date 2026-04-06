from __future__ import annotations

from itertools import cycle
from pathlib import Path
from xml.dom import minidom
import xml.etree.ElementTree as ET

import pandas as pd

from src.common.config import load_config


ZONE_ROUTE_MAP = {
    "A1": ["loop_nw", "west_spine"],
    "A2": ["north_spine", "teheran_loop"],
    "A3": ["east_spine", "upper_east_loop"],
    "B1": ["west_spine", "middle_loop_west"],
    "B2": ["core_loop", "gangnam_south_loop", "teheran_loop"],
    "B3": ["east_spine", "middle_loop_east"],
    "C1": ["south_west_loop", "south_spine"],
    "C2": ["gangnam_south_loop", "south_spine"],
    "C3": ["south_east_loop", "east_spine"],
}

ROUTES = {
    "loop_nw": "A0A1 A1B1 B1C1 C1C0 C0B0 B0A0",
    "north_spine": "A0A1 A1A2 A2B2 B2B1 B1B0 B0A0",
    "teheran_loop": "B2A2 A2A1 A1B1 B1B2",
    "upper_east_loop": "A2B2 B2B1 B1A1 A1A2",
    "west_spine": "A0B0 B0C0 C0C1 C1B1 B1A1 A1A0",
    "middle_loop_west": "B0B1 B1C1 C1C0 C0B0",
    "core_loop": "B1B2 B2C2 C2C1 C1B1",
    "gangnam_south_loop": "B2C2 C2C1 C1B1 B1B2",
    "middle_loop_east": "A2B2 B2C2 C2C1 C1B1 B1A1 A1A2",
    "east_spine": "A2B2 B2C2 C2C1 C1B1 B1A1 A1A2",
    "south_west_loop": "B0C0 C0C1 C1B1 B1B0",
    "south_spine": "C0C1 C1C2 C2B2 B2B1 B1B0 B0C0",
    "south_east_loop": "B1B2 B2C2 C2C1 C1B1",
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

    cfg = load_config()
    horizon_seconds = float(cfg["sumo"].get("horizon_seconds", 1800.0))
    vehicle_scale = float(cfg["sumo"].get("vehicle_scale", 1.0))
    all_departures: list[tuple[str, str, float]] = []
    for _, row in df.iterrows():
        vehicle_count = int(max(0, round(row[supply_column] * vehicle_scale)))
        route_choices = ZONE_ROUTE_MAP[row["zone_id"]]
        route_cycle = cycle(route_choices)
        for i in range(vehicle_count):
            if vehicle_count == 1:
                depart = 0.0
            else:
                depart = (i / max(vehicle_count - 1, 1)) * horizon_seconds
            route_id = next(route_cycle)
            vehicle_id = f"{label}_{row['zone_id']}_{i:03d}"
            all_departures.append((vehicle_id, route_id, depart))

    all_departures.sort(key=lambda item: item[2])
    for vehicle_id, route_id, depart in all_departures:
        ET.SubElement(
            routes,
            "vehicle",
            id=vehicle_id,
            type="taxi",
            route=route_id,
            depart=f"{depart:.1f}",
            departLane="best",
            departSpeed="max",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pretty_xml(routes), encoding="utf-8")
    print(f"saved: {output_path}")


def build_sumocfg(net_file: str, route_file: str, output_path: Path) -> None:
    cfg = load_config()
    horizon_seconds = int(cfg["sumo"].get("horizon_seconds", 1800))
    content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<configuration xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/sumoConfiguration.xsd\">
    <input>
        <net-file value=\"{net_file}\"/>
        <route-files value=\"{route_file}\"/>
    </input>
    <time>
        <begin value=\"0\"/>
        <end value=\"{horizon_seconds}\"/>
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

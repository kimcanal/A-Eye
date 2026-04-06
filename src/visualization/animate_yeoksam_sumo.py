from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from PIL import Image

from src.common.config import load_config


@dataclass
class Vehicle:
    vehicle_id: str
    depart: float
    route_points: list[tuple[float, float]]
    route_length: float


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return (dx * dx + dy * dy) ** 0.5


def _shape_points(shape: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for pair in shape.split():
        x_str, y_str = pair.split(",")
        points.append((float(x_str), float(y_str)))
    return points


def _polyline_length(points: list[tuple[float, float]]) -> float:
    return sum(_distance(points[i], points[i + 1]) for i in range(len(points) - 1))


def _concat_route(edge_shapes: dict[str, list[tuple[float, float]]], edge_ids: list[str]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for edge_id in edge_ids:
        shape = edge_shapes[edge_id]
        if not points:
            points.extend(shape)
            continue
        if points[-1] == shape[0]:
            points.extend(shape[1:])
        else:
            points.extend(shape)
    return points


def _position_along(points: list[tuple[float, float]], distance_target: float) -> tuple[float, float]:
    if distance_target <= 0:
        return points[0]

    traversed = 0.0
    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]
        segment_length = _distance(start, end)
        if traversed + segment_length >= distance_target:
            ratio = (distance_target - traversed) / max(segment_length, 1e-9)
            return (
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            )
        traversed += segment_length
    return points[-1]


def _load_network(net_file: Path) -> tuple[dict[str, list[tuple[float, float]]], list[list[tuple[float, float]]]]:
    root = ET.parse(net_file).getroot()
    edge_shapes: dict[str, list[tuple[float, float]]] = {}
    visible_segments: list[list[tuple[float, float]]] = []

    for edge in root.findall("edge"):
        edge_id = edge.attrib["id"]
        if edge_id.startswith(":"):
            continue
        lane = edge.find("lane")
        if lane is None or "shape" not in lane.attrib:
            continue
        shape = _shape_points(lane.attrib["shape"])
        edge_shapes[edge_id] = shape
        visible_segments.append(shape)

    return edge_shapes, visible_segments


def _load_vehicles(route_file: Path, edge_shapes: dict[str, list[tuple[float, float]]]) -> list[Vehicle]:
    root = ET.parse(route_file).getroot()
    routes = {route.attrib["id"]: route.attrib["edges"].split() for route in root.findall("route")}

    vehicles: list[Vehicle] = []
    for vehicle in root.findall("vehicle"):
        route_id = vehicle.attrib["route"]
        edge_ids = routes[route_id]
        route_points = _concat_route(edge_shapes, edge_ids)
        vehicles.append(
            Vehicle(
                vehicle_id=vehicle.attrib["id"],
                depart=float(vehicle.attrib["depart"]),
                route_points=route_points,
                route_length=_polyline_length(route_points),
            )
        )
    return vehicles


def _draw_panel(
    ax: plt.Axes,
    road_segments: list[list[tuple[float, float]]],
    vehicles: list[Vehicle],
    current_time: float,
    title: str,
    subtitle: str,
    display_speed: float,
) -> None:
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(-10, 210)
    ax.set_ylim(-10, 210)
    ax.set_aspect("equal")
    ax.axis("off")

    line_segments = [[segment[i], segment[i + 1]] for segment in road_segments for i in range(len(segment) - 1)]
    ax.add_collection(LineCollection(line_segments, colors="#cbd5e1", linewidths=2.6, zorder=1))

    positions_x: list[float] = []
    positions_y: list[float] = []
    hotspot_x: list[float] = []
    hotspot_y: list[float] = []

    for vehicle in vehicles:
        elapsed = current_time - vehicle.depart
        if elapsed < 0:
            continue
        travel_distance = elapsed * display_speed
        if travel_distance > vehicle.route_length:
            continue
        x, y = _position_along(vehicle.route_points, travel_distance)
        positions_x.append(x)
        positions_y.append(y)
        if "_B2_" in vehicle.vehicle_id or "_C2_" in vehicle.vehicle_id or "_A2_" in vehicle.vehicle_id:
            hotspot_x.append(x)
            hotspot_y.append(y)

    if positions_x:
        ax.scatter(positions_x, positions_y, s=48, c="#f59e0b", edgecolors="#7c2d12", linewidths=0.6, zorder=3)
    if hotspot_x:
        ax.scatter(hotspot_x, hotspot_y, s=70, c="#ef4444", edgecolors="white", linewidths=0.9, zorder=4)

    zone_centers = {
        "A1": (50, 150),
        "A2": (50, 100),
        "A3": (50, 50),
        "B1": (100, 150),
        "B2": (100, 100),
        "B3": (100, 50),
        "C1": (150, 150),
        "C2": (150, 100),
        "C3": (150, 50),
    }
    for zone_id, (x, y) in zone_centers.items():
        ax.text(x, y, zone_id, fontsize=10, color="#64748b", ha="center", va="center", zorder=2)

    ax.text(0, 219, title, fontsize=14, fontweight="bold", color="#0f172a", ha="left", va="bottom")
    ax.text(0, 208, subtitle, fontsize=10, color="#475569", ha="left", va="bottom")
    ax.text(
        210,
        219,
        f"t = {int(current_time)}s",
        fontsize=11,
        color="#334155",
        ha="right",
        va="bottom",
    )
    ax.text(
        210,
        -4,
        f"Visible taxis: {len(positions_x)}",
        fontsize=10,
        color="#475569",
        ha="right",
        va="top",
    )


def _frame_image(
    road_segments: list[list[tuple[float, float]]],
    before_vehicles: list[Vehicle],
    after_vehicles: list[Vehicle],
    current_time: float,
    display_speed: float,
) -> Image.Image:
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), facecolor="#ffffff")
    _draw_panel(
        axes[0],
        road_segments,
        before_vehicles,
        current_time,
        "Before",
        "Uniform taxi allocation",
        display_speed,
    )
    _draw_panel(
        axes[1],
        road_segments,
        after_vehicles,
        current_time,
        "After",
        "Rule-based reallocation toward B2 / C2 / A2",
        display_speed,
    )

    fig.suptitle(
        "Yeoksam 3x3 Taxi Motion Playback",
        fontsize=18,
        fontweight="bold",
        y=0.98,
        color="#0f172a",
    )
    fig.text(
        0.02,
        0.02,
        "This is a lightweight playback of SUMO route files to make vehicle motion visible without SUMO GUI.",
        fontsize=10,
        color="#475569",
    )

    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)
    return Image.open(buffer).convert("P")


def save_motion_gif(net_file: Path, before_route: Path, after_route: Path, output_gif: Path, cover_png: Path) -> None:
    edge_shapes, road_segments = _load_network(net_file)
    before_vehicles = _load_vehicles(before_route, edge_shapes)
    after_vehicles = _load_vehicles(after_route, edge_shapes)

    display_speed = 4.8
    frame_times = [i * 20 for i in range(61)]
    frames = [
        _frame_image(road_segments, before_vehicles, after_vehicles, current_time, display_speed)
        for current_time in frame_times
    ]

    output_gif.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        duration=140,
        loop=0,
    )
    frames[18].save(cover_png)
    print(f"saved: {output_gif}")
    print(f"saved: {cover_png}")


def main() -> None:
    cfg = load_config()
    root = Path(__file__).resolve().parents[2]
    sumo_cfg = cfg["sumo"]
    output_dir = root / "outputs" / "yeoksam_sumo"
    save_motion_gif(
        root / sumo_cfg["net_file"],
        root / sumo_cfg["before_route_output"],
        root / sumo_cfg["after_route_output"],
        output_dir / "yeoksam_sumo_motion.gif",
        output_dir / "yeoksam_sumo_motion_cover.png",
    )


if __name__ == "__main__":
    main()

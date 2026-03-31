from __future__ import annotations

from collections import defaultdict
from io import BytesIO
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image


ENTITY_STYLE = {
    "passenger": {"color": "#1f77b4", "marker": "o", "label": "Passenger", "size": 140},
    "taxi": {"color": "#f2c100", "marker": "s", "label": "Taxi", "size": 180},
    "autonomous_vehicle": {"color": "#d62728", "marker": "D", "label": "Autonomous", "size": 180},
    "obstacle": {"color": "#444444", "marker": "X", "label": "Obstacle", "size": 200},
    "sedan": {"color": "#2ca02c", "marker": "^", "label": "Sedan", "size": 120},
    "suv": {"color": "#9467bd", "marker": "^", "label": "SUV", "size": 120},
    "van": {"color": "#8c564b", "marker": "^", "label": "Van", "size": 120},
    "compact": {"color": "#17becf", "marker": "^", "label": "Compact", "size": 120},
}

ENTITY_CODE = {
    "passenger": "P",
    "taxi": "T",
    "autonomous_vehicle": "AV",
    "obstacle": "X",
    "sedan": "SE",
    "suv": "SU",
    "van": "V",
    "compact": "C",
}


def style_for(kind: str) -> dict:
    return ENTITY_STYLE.get(kind, {"color": "#7f7f7f", "marker": "o", "label": kind, "size": 120})


def infer_city_size(logs: list[dict]) -> tuple[int, int]:
    max_x = max(entity["x"] for step in logs for entity in step["entities"])
    max_y = max(entity["y"] for step in logs for entity in step["entities"])
    return max_x + 1, max_y + 1


def summarize_entities(entities: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for entity in entities:
        counts[entity["kind"]] += 1
    return dict(counts)


def make_count_badge(entities: list[dict]) -> str:
    counts = summarize_entities(entities)
    ordered = ["taxi", "passenger", "autonomous_vehicle", "obstacle", "sedan", "suv", "van", "compact"]
    parts = [f"{ENTITY_CODE[k]}{counts[k]}" for k in ordered if counts.get(k)]
    return " ".join(parts[:4]) if parts else f"N{len(entities)}"


def spread_positions(base_x: int, base_y: int, count: int) -> list[tuple[float, float]]:
    if count <= 1:
        return [(float(base_x), float(base_y))]

    slots = [
        (-0.26, 0.26),
        (0.0, 0.26),
        (0.26, 0.26),
        (-0.26, 0.0),
        (0.0, 0.0),
        (0.26, 0.0),
        (-0.26, -0.26),
        (0.0, -0.26),
        (0.26, -0.26),
        (-0.13, 0.13),
        (0.13, 0.13),
        (-0.13, -0.13),
        (0.13, -0.13),
        (-0.34, 0.13),
        (0.34, 0.13),
        (-0.34, -0.13),
        (0.34, -0.13),
    ]
    chosen = slots[:count]
    return [(base_x + dx, base_y + dy) for dx, dy in chosen]


def draw_city_background(ax: plt.Axes, width: int, height: int) -> None:
    road_color = "#384249"
    lane_color = "#f8fafc"
    block_color = "#f4f6f8"
    block_edge = "#cfd5dc"
    green_color = "#8fbc6b"

    ax.set_facecolor(road_color)
    for x in range(width):
        for y in range(height):
            block = FancyBboxPatch(
                (x - 0.42, y - 0.42),
                0.84,
                0.84,
                boxstyle="round,pad=0.02,rounding_size=0.05",
                facecolor=block_color,
                edgecolor=block_edge,
                linewidth=1.0,
                zorder=0,
            )
            ax.add_patch(block)
            park = Rectangle(
                (x - 0.26, y - 0.26),
                0.18,
                0.18,
                facecolor=green_color,
                edgecolor="none",
                alpha=0.25,
                zorder=0,
            )
            ax.add_patch(park)

    for x in range(width):
        ax.plot([x, x], [-0.5, height - 0.5], color=lane_color, linewidth=2.2, alpha=0.18, zorder=1)
    for y in range(height):
        ax.plot([-0.5, width - 0.5], [y, y], color=lane_color, linewidth=2.2, alpha=0.18, zorder=1)

    stripe_length = 0.035
    stripe_gap = 0.02
    for x in range(1, width):
        for y in range(height):
            start_y = y - 0.12
            for i in range(5):
                y0 = start_y + i * (stripe_length + stripe_gap)
                ax.add_patch(
                    Rectangle(
                        (x - 0.5, y0),
                        0.08,
                        stripe_length,
                        facecolor=lane_color,
                        edgecolor="none",
                        alpha=0.9,
                        zorder=1,
                    )
                )
                ax.add_patch(
                    Rectangle(
                        (x + 0.42, y0),
                        0.08,
                        stripe_length,
                        facecolor=lane_color,
                        edgecolor="none",
                        alpha=0.9,
                        zorder=1,
                    )
                )
    for y in range(1, height):
        for x in range(width):
            start_x = x - 0.12
            for i in range(5):
                x0 = start_x + i * (stripe_length + stripe_gap)
                ax.add_patch(
                    Rectangle(
                        (x0, y - 0.5),
                        stripe_length,
                        0.08,
                        facecolor=lane_color,
                        edgecolor="none",
                        alpha=0.9,
                        zorder=1,
                    )
                )
                ax.add_patch(
                    Rectangle(
                        (x0, y + 0.42),
                        stripe_length,
                        0.08,
                        facecolor=lane_color,
                        edgecolor="none",
                        alpha=0.9,
                        zorder=1,
                    )
                )


def add_step_summary(ax: plt.Axes, step_log: dict) -> None:
    counts = summarize_entities(step_log["entities"])
    ordered = [
        ("taxi", "Taxi"),
        ("passenger", "Passenger"),
        ("autonomous_vehicle", "Autonomous"),
        ("obstacle", "Obstacle"),
    ]
    summary_lines = [f"{label}: {counts.get(kind, 0)}" for kind, label in ordered]
    ax.text(
        0.01,
        1.02,
        " | ".join(summary_lines),
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        color="#374151",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#ffffff", "edgecolor": "#d1d5db", "alpha": 0.95},
    )


def render_step(step_log: dict, city_size: tuple[int, int]) -> Image.Image:
    width, height = city_size
    fig, ax = plt.subplots(figsize=(9.5, 8.2))
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_xticks(range(width))
    ax.set_yticks(range(height))
    ax.set_aspect("equal")
    draw_city_background(ax, width, height)
    ax.grid(False)
    ax.set_title(f"Module 1 Digital Twin Snapshot - Step {step_log['step']}", fontsize=19, pad=24)
    ax.set_xlabel("City X block", fontsize=13)
    ax.set_ylabel("City Y block", fontsize=13)
    add_step_summary(ax, step_log)

    legend_items: dict[str, Line2D] = {}
    grouped: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for entity in step_log["entities"]:
        grouped[(entity["x"], entity["y"])].append(entity)

    label_kinds = {"taxi", "autonomous_vehicle", "obstacle"}

    for (base_x, base_y), entities in grouped.items():
        entities = sorted(entities, key=lambda e: (e["kind"], e["entity_id"]))
        positions = spread_positions(base_x, base_y, len(entities))

        if len(entities) > 1:
            ax.text(
                base_x - 0.40,
                base_y + 0.36,
                make_count_badge(entities),
                fontsize=7.5,
                color="#374151",
                bbox={"boxstyle": "round,pad=0.18", "facecolor": "#ffffff", "edgecolor": "#d1d5db", "alpha": 0.94},
                zorder=2,
            )

        for entity, (plot_x, plot_y) in zip(entities, positions):
            style = style_for(entity["kind"])
            ax.scatter(
                plot_x,
                plot_y,
                s=style["size"],
                c=style["color"],
                marker=style["marker"],
                edgecolors="#111827",
                linewidths=0.8,
                alpha=0.97,
                zorder=3,
            )
            if entity["kind"] in label_kinds:
                ax.text(
                    plot_x + 0.04,
                    plot_y + 0.04,
                    entity["entity_id"],
                    fontsize=7,
                    color="#111827",
                    zorder=4,
                )
            if entity["kind"] not in legend_items:
                legend_items[entity["kind"]] = Line2D(
                    [0],
                    [0],
                    marker=style["marker"],
                    color="w",
                    label=style["label"],
                    markerfacecolor=style["color"],
                    markeredgecolor="#111827",
                    markersize=9,
                )

    events = step_log.get("events", [])
    event_text = "\n".join(events[:5]) if events else "No events"
    if len(events) > 5:
        event_text += "\n..."
    ax.text(
        1.02,
        0.98,
        f"Latest Events\n{event_text}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        bbox={"boxstyle": "round,pad=0.55", "facecolor": "white", "edgecolor": "#d1d5db"},
    )

    ax.legend(
        handles=list(legend_items.values()),
        loc="lower left",
        bbox_to_anchor=(1.02, 0.02),
        frameon=True,
        title="Entity Types",
        title_fontsize=11,
        fontsize=10,
    )
    plt.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def render_from_log(log_path: Path, output_dir: Path) -> dict[str, str]:
    logs = json.loads(log_path.read_text(encoding="utf-8"))
    city_size = infer_city_size(logs)

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    images: list[Image.Image] = []
    frame_paths: list[str] = []
    for step_log in logs:
        image = render_step(step_log, city_size)
        frame_path = frames_dir / f"step_{step_log['step']:02d}.png"
        image.save(frame_path)
        images.append(image)
        frame_paths.append(str(frame_path))

    overview_path = output_dir / "module1_overview.png"
    images[-1].save(overview_path)

    gif_path = output_dir / "module1_simulation.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=900,
        loop=0,
    )

    return {
        "overview_image": str(overview_path),
        "animation_gif": str(gif_path),
        "frames_dir": str(frames_dir),
        "frame_count": len(images),
        "frame_paths": frame_paths,
    }

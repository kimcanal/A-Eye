from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
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


def style_for(kind: str) -> dict:
    return ENTITY_STYLE.get(kind, {"color": "#7f7f7f", "marker": "o", "label": kind, "size": 120})


def infer_city_size(logs: list[dict]) -> tuple[int, int]:
    max_x = max(entity["x"] for step in logs for entity in step["entities"])
    max_y = max(entity["y"] for step in logs for entity in step["entities"])
    return max_x + 1, max_y + 1


def render_step(step_log: dict, city_size: tuple[int, int]) -> Image.Image:
    width, height = city_size
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_xticks(range(width))
    ax.set_yticks(range(height))
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", linewidth=0.8, alpha=0.4)
    ax.set_facecolor("#f8fafc")
    ax.set_title(f"Module 1 City Snapshot - Step {step_log['step']}")
    ax.set_xlabel("X block")
    ax.set_ylabel("Y block")

    legend_items: dict[str, Line2D] = {}
    for entity in step_log["entities"]:
        style = style_for(entity["kind"])
        ax.scatter(
            entity["x"],
            entity["y"],
            s=style["size"],
            c=style["color"],
            marker=style["marker"],
            edgecolors="#111827",
            linewidths=0.8,
            alpha=0.95,
            zorder=3,
        )
        ax.text(
            entity["x"] + 0.06,
            entity["y"] + 0.06,
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
        f"Events\n{event_text}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#d1d5db"},
    )

    ax.legend(
        handles=list(legend_items.values()),
        loc="lower left",
        bbox_to_anchor=(1.02, 0.02),
        frameon=True,
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

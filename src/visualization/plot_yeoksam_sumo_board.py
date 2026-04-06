from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import Rectangle
import pandas as pd

from src.common.config import load_config


ZONE_ORDER = [
    "A1", "A2", "A3",
    "B1", "B2", "B3",
    "C1", "C2", "C3",
]


def _zone_position(zone_id: str) -> tuple[int, int]:
    row = ord(zone_id[0]) - ord("A")
    col = int(zone_id[1]) - 1
    return row, col


def _grid_df(df: pd.DataFrame) -> pd.DataFrame:
    ordered = df.set_index("zone_id").reindex(ZONE_ORDER).reset_index()
    return ordered


def _draw_grid(
    ax: plt.Axes,
    df: pd.DataFrame,
    value_column: str,
    title: str,
    cmap_name: str,
    value_label: str,
    zone_label_column: str = "zone_name",
) -> None:
    values = df[value_column].astype(float)
    vmin = float(values.min())
    vmax = float(values.max())
    if vmin == vmax:
        vmax = vmin + 1.0
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap(cmap_name)

    ax.set_xlim(0, 3)
    ax.set_ylim(3, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)

    for _, row in df.iterrows():
        zone_id = row["zone_id"]
        grid_row, grid_col = _zone_position(zone_id)
        value = float(row[value_column])
        color = cmap(norm(value))
        rect = Rectangle((grid_col, grid_row), 1, 1, facecolor=color, edgecolor="white", linewidth=2)
        ax.add_patch(rect)

        zone_name = str(row.get(zone_label_column, zone_id))
        short_name = zone_name.replace("Gangnam Station ", "").replace("Yeoksam ", "")
        short_name = short_name.replace("Gangnam-daero ", "")

        ax.text(
            grid_col + 0.08,
            grid_row + 0.18,
            zone_id,
            fontsize=10,
            fontweight="bold",
            color="#111827",
            va="top",
        )
        ax.text(
            grid_col + 0.08,
            grid_row + 0.43,
            short_name,
            fontsize=8,
            color="#1f2937",
            va="top",
        )
        ax.text(
            grid_col + 0.5,
            grid_row + 0.78,
            f"{value:g}",
            fontsize=16,
            fontweight="bold",
            color="#111827",
            ha="center",
            va="center",
        )

    ax.text(
        0,
        3.15,
        value_label,
        fontsize=9,
        color="#4b5563",
        va="bottom",
    )


def _draw_summary(ax: plt.Axes, comparison_df: pd.DataFrame, evaluation: dict) -> None:
    ax.axis("off")
    before = evaluation["before"]
    after = evaluation["after"]

    top_hotspots = comparison_df.sort_values("dispatch_rank").head(4)
    hotspot_lines = [
        f"{row.zone_id}: {row.zone_name} (demand {row.dispatch_demand:g}, taxis +{int(max(row.taxis_moved, 0))})"
        for row in top_hotspots.itertuples()
    ]

    moved_out = comparison_df[comparison_df["taxis_moved"] < 0].sort_values("taxis_moved")
    moved_out_lines = [
        f"{row.zone_id}: -{abs(int(row.taxis_moved))} taxi(s)"
        for row in moved_out.itertuples()
        if int(row.taxis_moved) != 0
    ]

    summary = "\n".join(
        [
            "Yeoksam 3x3 SUMO Baseline",
            "",
            f"Timestamp: {evaluation['timestamp']}",
            f"Strategy: {evaluation['strategy']}",
            "",
            "Before vs After",
            f"- Total shortage: {before['total_shortage']:.0f} -> {after['total_shortage']:.0f}",
            f"- Max shortage: {before['max_shortage']:.0f} -> {after['max_shortage']:.0f}",
            f"- Mean abs gap: {before['mean_abs_gap']:.2f} -> {after['mean_abs_gap']:.2f}",
            "",
            "Main hotspot allocation",
            *[f"- {line}" for line in hotspot_lines],
            "",
            "Taxis moved out of low-demand cells",
            *([f"- {line}" for line in moved_out_lines] if moved_out_lines else ["- none"]),
        ]
    )

    ax.text(
        0.0,
        1.0,
        summary,
        fontsize=11,
        color="#111827",
        va="top",
        ha="left",
        linespacing=1.5,
        family="DejaVu Sans",
    )


def save_dashboard(comparison_csv: Path, evaluation_json: Path, output: Path) -> None:
    comparison_df = pd.read_csv(comparison_csv)
    comparison_df = _grid_df(comparison_df)
    evaluation = json.loads(evaluation_json.read_text(encoding="utf-8"))

    fig = plt.figure(figsize=(18, 11), facecolor="#f8fafc")
    gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1, 1.15], height_ratios=[1, 1], wspace=0.18, hspace=0.22)

    _draw_grid(fig.add_subplot(gs[0, 0]), comparison_df, "dispatch_demand", "Demand Hotspots", "YlOrRd", "Observed 5-minute demand at the latest step")
    _draw_grid(fig.add_subplot(gs[0, 1]), comparison_df, "baseline_before_taxis", "Before Supply", "Blues", "Market-cruise patrol distribution before dispatch")
    _draw_grid(fig.add_subplot(gs[0, 2]), comparison_df, "reallocated_taxis", "After Supply", "Blues", "Kakao-like heuristic reallocation toward hotspot cells")
    _draw_summary(fig.add_subplot(gs[:, 3]), comparison_df, evaluation)
    _draw_grid(fig.add_subplot(gs[1, 0]), comparison_df, "before_shortage", "Before Shortage", "OrRd", "Higher value means more unmet demand")
    _draw_grid(fig.add_subplot(gs[1, 1]), comparison_df, "after_shortage", "After Shortage", "OrRd", "Shortage after reallocation")
    _draw_grid(fig.add_subplot(gs[1, 2]), comparison_df, "taxis_moved", "Taxi Reallocation", "PiYG", "Positive = taxis moved in, negative = moved out")

    fig.suptitle(
        "Yeoksam SUMO Before/After Dispatch Board",
        fontsize=18,
        fontweight="bold",
        y=0.98,
        color="#0f172a",
    )
    fig.text(
        0.05,
        0.95,
        "A 3x3 summary board that makes the patrol-vs-dispatch change readable without SUMO GUI",
        fontsize=11,
        color="#475569",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"saved: {output}")


def main() -> None:
    cfg = load_config()
    output = Path(cfg["visualization"].get("yeoksam_dashboard_output", "outputs/yeoksam_sumo/yeoksam_sumo_board.png"))
    save_dashboard(
        Path(cfg["analysis"]["dispatch_comparison_output"]),
        Path(cfg["analysis"]["dispatch_eval_output"]),
        output,
    )


if __name__ == "__main__":
    main()

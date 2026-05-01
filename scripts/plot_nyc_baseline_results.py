from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
METRICS_PATH = ROOT_DIR / "data" / "processed" / "model" / "nyc_baseline_metrics.json"
PREDICTION_SAMPLE_PATH = (
    ROOT_DIR / "data" / "processed" / "model" / "nyc_baseline_prediction_sample.csv"
)
NYC_HOURLY_PATTERN_PATH = (
    WORKSPACE_DIR
    / "a-eye-us-taxi-transfer"
    / "processed"
    / "nyc_yellow_2025_01_2026_03_manhattan_hourly_pattern.csv"
)
FIGURE_DIR = ROOT_DIR / "data" / "processed" / "model" / "figures"
REPORT_PATH = ROOT_DIR / "docs" / "NYC_BASELINE_MODEL.md"


COLORS = {
    "ridge_model": "#2563eb",
    "persistence_baseline": "#f97316",
    "rolling_1h_baseline": "#16a34a",
    "weekday": "#2563eb",
    "weekend": "#dc2626",
    "axis": "#1f2937",
    "grid": "#e5e7eb",
    "text": "#111827",
    "muted": "#6b7280",
}

MODEL_LABELS = {
    "ridge_model": "Ridge",
    "persistence_baseline": "Persistence",
    "rolling_1h_baseline": "Rolling 1h",
}


def write_svg(path: Path, body: str, width: int = 920, height: int = 520) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <style>
    text {{ font-family: Arial, sans-serif; fill: {COLORS['text']}; }}
    .title {{ font-size: 22px; font-weight: 700; }}
    .subtitle {{ font-size: 13px; fill: {COLORS['muted']}; }}
    .label {{ font-size: 12px; fill: {COLORS['muted']}; }}
    .tick {{ font-size: 11px; fill: {COLORS['muted']}; }}
  </style>
{body}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def scale(value: float, domain_min: float, domain_max: float, range_min: float, range_max: float) -> float:
    if domain_max <= domain_min:
        return (range_min + range_max) / 2
    ratio = (value - domain_min) / (domain_max - domain_min)
    return range_min + ratio * (range_max - range_min)


def load_metrics() -> dict[str, object]:
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


def load_prediction_sample() -> list[dict[str, str]]:
    with PREDICTION_SAMPLE_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_hourly_pattern() -> list[dict[str, str]]:
    with NYC_HOURLY_PATTERN_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def draw_metric_bars(payload: dict[str, object]) -> Path:
    metrics = payload["metrics"]
    top5 = payload["top5_overlap"]
    panels = [
        ("RMSE lower is better", "rmse", False),
        ("R2 higher is better", "r2", True),
        ("Top-5 overlap higher is better", "top5", True),
    ]
    width, height = 920, 520
    left, top = 72, 86
    panel_w, panel_h, gap = 240, 300, 36
    body = [
        '<text x="40" y="42" class="title">NYC t+5min Demand Model Metrics</text>',
        '<text x="40" y="64" class="subtitle">Ridge baseline is compared against simple temporal baselines on March 2026 test data.</text>',
    ]
    models = ["ridge_model", "persistence_baseline", "rolling_1h_baseline"]
    for panel_index, (title, key, higher_better) in enumerate(panels):
        x0 = left + panel_index * (panel_w + gap)
        y0 = top
        if key == "top5":
            values = {model: float(top5[model]) for model in models}
        else:
            values = {model: float(metrics[model][key]) for model in models}
        max_value = max(values.values()) * 1.12
        body.append(f'<text x="{x0}" y="{y0 - 20}" class="label">{escape(title)}</text>')
        body.append(f'<line x1="{x0}" y1="{y0 + panel_h}" x2="{x0 + panel_w}" y2="{y0 + panel_h}" stroke="{COLORS["axis"]}" stroke-width="1"/>')
        for tick in range(5):
            y = y0 + panel_h - tick * panel_h / 4
            v = max_value * tick / 4
            body.append(f'<line x1="{x0}" y1="{y}" x2="{x0 + panel_w}" y2="{y}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
            body.append(f'<text x="{x0 - 8}" y="{y + 4}" text-anchor="end" class="tick">{v:.2f}</text>')
        bar_w = 52
        for index, model in enumerate(models):
            value = values[model]
            bar_h = scale(value, 0, max_value, 0, panel_h)
            x = x0 + 28 + index * 72
            y = y0 + panel_h - bar_h
            body.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" fill="{COLORS[model]}" rx="4"/>')
            body.append(f'<text x="{x + bar_w / 2}" y="{y - 8}" text-anchor="middle" class="tick">{value:.3f}</text>')
            body.append(f'<text x="{x + bar_w / 2}" y="{y0 + panel_h + 22}" text-anchor="middle" class="tick">{MODEL_LABELS[model]}</text>')
    body.append('<text x="40" y="480" class="subtitle">Ridge improves RMSE and ranking overlap against the two simple baselines.</text>')
    path = FIGURE_DIR / "nyc_baseline_metrics.svg"
    write_svg(path, "\n".join(body), width, height)
    return path


def draw_hourly_pattern(rows: list[dict[str, str]]) -> Path:
    width, height = 920, 520
    x0, y0, plot_w, plot_h = 76, 88, 780, 310
    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for row in rows:
        grouped[row["day_type"]].append(
            (int(row["service_hour"]), float(row["avg_zone_5min_pickups"]))
        )
    max_value = max(value for values in grouped.values() for _, value in values) * 1.1
    body = [
        '<text x="40" y="42" class="title">NYC Hourly Taxi Demand Pattern</text>',
        '<text x="40" y="64" class="subtitle">Average Manhattan zone pickups per 5-minute bucket, 2025-01 through 2026-03.</text>',
    ]
    for tick in range(6):
        y = y0 + plot_h - tick * plot_h / 5
        v = max_value * tick / 5
        body.append(f'<line x1="{x0}" y1="{y}" x2="{x0 + plot_w}" y2="{y}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        body.append(f'<text x="{x0 - 10}" y="{y + 4}" text-anchor="end" class="tick">{v:.1f}</text>')
    for hour in range(0, 25, 3):
        x = scale(hour, 0, 23, x0, x0 + plot_w)
        body.append(f'<text x="{x}" y="{y0 + plot_h + 24}" text-anchor="middle" class="tick">{hour if hour < 24 else ""}</text>')
    body.append(f'<line x1="{x0}" y1="{y0 + plot_h}" x2="{x0 + plot_w}" y2="{y0 + plot_h}" stroke="{COLORS["axis"]}" stroke-width="1"/>')
    body.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + plot_h}" stroke="{COLORS["axis"]}" stroke-width="1"/>')
    for day_type in ["weekday", "weekend"]:
        points = sorted(grouped[day_type])
        coords = [
            f"{scale(hour, 0, 23, x0, x0 + plot_w):.2f},{scale(value, 0, max_value, y0 + plot_h, y0):.2f}"
            for hour, value in points
        ]
        body.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{COLORS[day_type]}" stroke-width="3"/>')
        for hour, value in points:
            cx = scale(hour, 0, 23, x0, x0 + plot_w)
            cy = scale(value, 0, max_value, y0 + plot_h, y0)
            body.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{COLORS[day_type]}"/>')
    body.append(f'<rect x="690" y="88" width="160" height="54" fill="#ffffff" stroke="{COLORS["grid"]}" rx="6"/>')
    body.append(f'<circle cx="712" cy="108" r="5" fill="{COLORS["weekday"]}"/><text x="726" y="113" class="label">weekday</text>')
    body.append(f'<circle cx="712" cy="130" r="5" fill="{COLORS["weekend"]}"/><text x="726" y="135" class="label">weekend</text>')
    body.append('<text x="410" y="454" text-anchor="middle" class="label">Hour of day</text>')
    body.append('<text x="22" y="250" transform="rotate(-90 22 250)" text-anchor="middle" class="label">Avg zone pickups / 5min</text>')
    path = FIGURE_DIR / "nyc_hourly_pattern.svg"
    write_svg(path, "\n".join(body), width, height)
    return path


def draw_prediction_scatter(rows: list[dict[str, str]]) -> Path:
    width, height = 920, 520
    x0, y0, plot_w, plot_h = 82, 90, 760, 320
    points = [
        (float(row["actual_t_plus_5"]), float(row["predicted_t_plus_5"]))
        for row in rows
    ]
    max_value = max(max(actual, pred) for actual, pred in points) * 1.08
    body = [
        '<text x="40" y="42" class="title">Actual vs Predicted t+5min Pickups</text>',
        '<text x="40" y="64" class="subtitle">Largest-error sample exported from the March 2026 test set. Diagonal line is perfect prediction.</text>',
    ]
    for tick in range(6):
        x = x0 + tick * plot_w / 5
        y = y0 + plot_h - tick * plot_h / 5
        v = max_value * tick / 5
        body.append(f'<line x1="{x0}" y1="{y}" x2="{x0 + plot_w}" y2="{y}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        body.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0 + plot_h}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        body.append(f'<text x="{x0 - 10}" y="{y + 4}" text-anchor="end" class="tick">{v:.0f}</text>')
        body.append(f'<text x="{x}" y="{y0 + plot_h + 22}" text-anchor="middle" class="tick">{v:.0f}</text>')
    body.append(f'<line x1="{x0}" y1="{y0 + plot_h}" x2="{x0 + plot_w}" y2="{y0 + plot_h}" stroke="{COLORS["axis"]}" stroke-width="1"/>')
    body.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + plot_h}" stroke="{COLORS["axis"]}" stroke-width="1"/>')
    body.append(f'<line x1="{x0}" y1="{y0 + plot_h}" x2="{x0 + plot_w}" y2="{y0}" stroke="#9ca3af" stroke-dasharray="6 6" stroke-width="2"/>')
    for actual, pred in points:
        cx = scale(actual, 0, max_value, x0, x0 + plot_w)
        cy = scale(pred, 0, max_value, y0 + plot_h, y0)
        body.append(f'<circle cx="{cx}" cy="{cy}" r="3.2" fill="#2563eb" opacity="0.42"/>')
    body.append('<text x="462" y="462" text-anchor="middle" class="label">Actual pickups at t+5min</text>')
    body.append('<text x="24" y="250" transform="rotate(-90 24 250)" text-anchor="middle" class="label">Predicted pickups at t+5min</text>')
    path = FIGURE_DIR / "nyc_actual_vs_predicted.svg"
    write_svg(path, "\n".join(body), width, height)
    return path


def draw_error_by_zone_type(rows: list[dict[str, str]]) -> Path:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row["zone_type"]].append(float(row["absolute_error"]))
    values = {
        zone_type: sum(errors) / len(errors)
        for zone_type, errors in grouped.items()
        if errors
    }
    ordered = sorted(values.items(), key=lambda item: item[1], reverse=True)
    width, height = 920, 520
    x0, y0, plot_w, plot_h = 210, 88, 600, 300
    max_value = max(values.values()) * 1.15
    body = [
        '<text x="40" y="42" class="title">Largest-Error Sample by Zone Type</text>',
        '<text x="40" y="64" class="subtitle">Mean absolute error from the exported largest-error sample. Use as diagnostics, not population-level error.</text>',
    ]
    for tick in range(6):
        x = x0 + tick * plot_w / 5
        v = max_value * tick / 5
        body.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0 + plot_h}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        body.append(f'<text x="{x}" y="{y0 + plot_h + 22}" text-anchor="middle" class="tick">{v:.0f}</text>')
    bar_h = 38
    for index, (zone_type, value) in enumerate(ordered):
        y = y0 + index * 54
        w = scale(value, 0, max_value, 0, plot_w)
        body.append(f'<text x="{x0 - 14}" y="{y + 25}" text-anchor="end" class="label">{escape(zone_type)}</text>')
        body.append(f'<rect x="{x0}" y="{y}" width="{w}" height="{bar_h}" fill="#2563eb" rx="5"/>')
        body.append(f'<text x="{x0 + w + 8}" y="{y + 25}" class="tick">{value:.1f}</text>')
    body.append('<text x="510" y="456" text-anchor="middle" class="label">Mean absolute error</text>')
    path = FIGURE_DIR / "nyc_error_by_zone_type.svg"
    write_svg(path, "\n".join(body), width, height)
    return path


def update_report(paths: list[Path]) -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")
    marker = "## Figures"
    figure_lines = [
        "## Figures",
        "",
        "- `data/processed/model/figures/nyc_baseline_metrics.svg`",
        "- `data/processed/model/figures/nyc_hourly_pattern.svg`",
        "- `data/processed/model/figures/nyc_actual_vs_predicted.svg`",
        "- `data/processed/model/figures/nyc_error_by_zone_type.svg`",
        "",
    ]
    if marker in report:
        report = report.split(marker)[0].rstrip() + "\n\n"
    report = report.rstrip() + "\n\n" + "\n".join(figure_lines)
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    metrics = load_metrics()
    prediction_sample = load_prediction_sample()
    hourly_pattern = load_hourly_pattern()
    paths = [
        draw_metric_bars(metrics),
        draw_hourly_pattern(hourly_pattern),
        draw_prediction_scatter(prediction_sample),
        draw_error_by_zone_type(prediction_sample),
    ]
    update_report(paths)
    print(json.dumps({"figures": [str(path.relative_to(ROOT_DIR)) for path in paths]}, indent=2))


if __name__ == "__main__":
    main()

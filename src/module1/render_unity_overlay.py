#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CAPSTONE_ROOT = Path("/Users/kenny31/Documents/Capstone")
BASE_IMAGE = CAPSTONE_ROOT / "outputs" / "module1" / "unity_module1_view.png"
POINTS_JSON = CAPSTONE_ROOT / "outputs" / "module1" / "unity_overlay_points.json"
OUTPUT_IMAGE = CAPSTONE_ROOT / "outputs" / "module1" / "unity_module1_annotated.png"


def load_font(size: int) -> ImageFont.ImageFont:
    for path in [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]:
        font_path = Path(path)
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def rank_color(rank: int) -> tuple[int, int, int]:
    if rank == 1:
        return (245, 129, 32)
    if rank == 2:
        return (247, 184, 46)
    if rank == 3:
        return (255, 214, 92)
    return (180, 180, 180)


def short_zone(zone_id: str) -> str:
    zone_id = str(zone_id)
    return zone_id[-4:] if len(zone_id) > 4 else zone_id


def short_hotspot(label: str) -> str:
    mapping = {
        "West Gate": "West",
        "South Hub": "South",
        "East Connector": "East",
    }
    return mapping.get(label, label)


def draw_badge(draw: ImageDraw.ImageDraw, x: float, y: float, rank: int, zone_id: str, hotspot: str) -> None:
    color = rank_color(rank)
    radius = 18
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline=(255, 255, 255), width=4)

    font_small = load_font(22)
    font_body = load_font(24)
    rank_text = f"R{rank}"
    draw.text((x, y - 1), rank_text, fill=(20, 20, 20), font=font_small, anchor="mm")

    label = f"{short_zone(zone_id)} · {short_hotspot(hotspot)}"
    text_bbox = draw.textbbox((0, 0), label, font=font_body)
    pad_x = 12
    pad_y = 8
    box_w = (text_bbox[2] - text_bbox[0]) + pad_x * 2
    box_h = (text_bbox[3] - text_bbox[1]) + pad_y * 2
    box_x0 = x + 22
    box_y0 = y - box_h - 18
    box_x1 = box_x0 + box_w
    box_y1 = box_y0 + box_h

    draw.line((x + radius * 0.75, y - radius * 0.75, box_x0, box_y1), fill=color, width=3)
    draw.rounded_rectangle((box_x0, box_y0, box_x1, box_y1), radius=12, fill=(255, 255, 255, 230), outline=color, width=3)
    draw.text((box_x0 + pad_x, box_y0 + pad_y), label, fill=(28, 28, 28), font=font_body)


def spread_points(points: list[dict], width: int, height: int) -> list[tuple[dict, float, float]]:
    projected: list[tuple[dict, float, float]] = []
    for point in points:
        x = float(point["viewport_x"]) * width
        y = (1.0 - float(point["viewport_y"])) * height
        projected.append((point, x, y))

    if not projected:
        return projected

    base_x = sum(item[1] for item in projected) / len(projected)
    base_y = sum(item[2] for item in projected) / len(projected)
    offsets = [(-120, 18), (0, -58), (120, 18), (-180, 82), (180, 82)]

    adjusted: list[tuple[dict, float, float]] = []
    for index, (point, x, y) in enumerate(sorted(projected, key=lambda item: int(item[0]["dispatch_rank"]))):
        if len(projected) > 1:
            dx, dy = offsets[index % len(offsets)]
            x = base_x + dx
            y = base_y + dy
        x = min(max(x, 60), width - 220)
        y = min(max(y, 80), height - 80)
        adjusted.append((point, x, y))

    return adjusted


def main() -> None:
    if not BASE_IMAGE.exists() or not POINTS_JSON.exists():
        raise FileNotFoundError("Unity base image or overlay points JSON is missing.")

    image = Image.open(BASE_IMAGE).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    payload = json.loads(POINTS_JSON.read_text(encoding="utf-8"))
    points = payload.get("points", [])

    width, height = image.size
    for point, x, y in spread_points(points, width, height):
        draw_badge(
            draw,
            x,
            y,
            int(point["dispatch_rank"]),
            str(point["zone_id"]),
            str(point["hotspot_label"]),
        )

    title_font = load_font(30)
    subtitle_font = load_font(22)
    draw.rounded_rectangle((26, 24, 420, 106), radius=18, fill=(255, 255, 255, 215), outline=(50, 50, 50), width=2)
    draw.text((46, 38), "Module 1 Dispatch Overlay", fill=(20, 20, 20), font=title_font)
    draw.text((46, 74), "Top 3 predicted dispatch hotspots", fill=(70, 70, 70), font=subtitle_font)

    out = Image.alpha_composite(image, overlay)
    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUTPUT_IMAGE)
    print(f"Saved annotated image: {OUTPUT_IMAGE}")


if __name__ == "__main__":
    main()

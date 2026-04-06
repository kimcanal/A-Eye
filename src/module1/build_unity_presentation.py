#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


CAPSTONE_ROOT = Path(__file__).resolve().parents[2]
MODULE1_OUTPUTS = CAPSTONE_ROOT / "outputs" / "module1"
ANNOTATED_IMAGE = MODULE1_OUTPUTS / "unity_module1_annotated.png"
VIEW_IMAGE = MODULE1_OUTPUTS / "unity_module1_view.png"
POINTS_JSON = MODULE1_OUTPUTS / "unity_overlay_points.json"
SCENARIO_JSON = MODULE1_OUTPUTS / "unity_scenario.json"
OUTPUT_IMAGE = MODULE1_OUTPUTS / "unity_module1_presentation.png"


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for path in candidates:
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
    return (186, 186, 186)


def enhance_image(image: Image.Image) -> Image.Image:
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Color(image).enhance(1.06)
    image = ImageEnhance.Sharpness(image).enhance(1.18)
    return image


def add_shadow(base: Image.Image, card: Image.Image, x: int, y: int, blur_radius: int = 16) -> None:
    shadow = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(shadow)
    draw.rounded_rectangle(
        (x + 8, y + 10, x + card.width + 8, y + card.height + 10),
        radius=24,
        fill=(21, 39, 61, 52),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    base.alpha_composite(shadow)
    base.alpha_composite(card, (x, y))


def fit_image(image: Image.Image, box_w: int, box_h: int) -> Image.Image:
    img = image.copy()
    img.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
    return img


def short_zone(zone_id: str) -> str:
    zone_id = str(zone_id)
    return zone_id[-4:] if len(zone_id) > 4 else zone_id


def read_points() -> list[dict]:
    payload = json.loads(POINTS_JSON.read_text(encoding="utf-8"))
    return payload.get("points", [])


def read_scenario() -> dict:
    return json.loads(SCENARIO_JSON.read_text(encoding="utf-8"))


def zoom_crop(image: Image.Image, points: list[dict]) -> Image.Image:
    if not points:
        return image.copy()

    width, height = image.size
    px = [float(point["viewport_x"]) * width for point in points]
    py = [(1.0 - float(point["viewport_y"])) * height for point in points]
    min_x, max_x = min(px), max(px)
    min_y, max_y = min(py), max(py)

    pad_x = 280
    pad_y = 240
    x0 = max(int(min_x - pad_x), 0)
    y0 = max(int(min_y - pad_y), 0)
    x1 = min(int(max_x + pad_x), width)
    y1 = min(int(max_y + pad_y), height)

    crop = image.crop((x0, y0, x1, y1)).convert("RGBA")
    crop = enhance_image(crop)
    draw = ImageDraw.Draw(crop)
    font = load_font(26, bold=True)

    for point in sorted(points, key=lambda item: int(item["dispatch_rank"])):
        local_x = float(point["viewport_x"]) * width - x0
        local_y = (1.0 - float(point["viewport_y"])) * height - y0
        color = rank_color(int(point["dispatch_rank"]))
        radius = 26
        draw.ellipse(
            (local_x - radius, local_y - radius, local_x + radius, local_y + radius),
            fill=color,
            outline=(255, 255, 255),
            width=5,
        )
        draw.text((local_x, local_y), f"R{point['dispatch_rank']}", fill=(24, 24, 24), font=font, anchor="mm")

    return crop


def build_hotspot_cards(draw: ImageDraw.ImageDraw, scenario: dict, x: int, y: int, width: int) -> int:
    title_font = load_font(28, bold=True)
    text_font = load_font(19)
    draw.text((x, y), "Top Dispatch Hotspots", fill=(248, 250, 252), font=title_font)
    y += 52

    for taxi in scenario.get("taxis", []):
        card_h = 96
        color = rank_color(int(taxi["dispatch_rank"]))
        draw.rounded_rectangle(
            (x, y, x + width, y + card_h),
            radius=20,
            fill=(19, 33, 54),
            outline=(56, 77, 104),
            width=2,
        )
        draw.rounded_rectangle((x + 16, y + 18, x + 84, y + 86), radius=18, fill=color)
        rank_font = load_font(28, bold=True)
        draw.text((x + 50, y + 52), f"R{taxi['dispatch_rank']}", fill=(32, 32, 32), font=rank_font, anchor="mm")
        draw.text(
            (x + 100, y + 18),
            f"Zone {short_zone(taxi['zone_id'])} · {taxi['hotspot_label']}",
            fill=(248, 250, 252),
            font=load_font(20, bold=True),
        )
        draw.text(
            (x + 100, y + 48),
            f"Predicted demand {taxi['predicted_call_count']:.2f} / Supply {taxi['available_taxis']:.0f}",
            fill=(202, 213, 225),
            font=text_font,
        )
        draw.text(
            (x + 100, y + 72),
            f"Imbalance {taxi['imbalance_score']:.3f} · Incentive x{taxi['incentive_multiplier']:.2f}",
            fill=(202, 213, 225),
            font=text_font,
        )
        y += card_h + 14

    return y


def main() -> None:
    annotated = enhance_image(Image.open(ANNOTATED_IMAGE).convert("RGBA"))
    view = Image.open(VIEW_IMAGE).convert("RGBA")
    points = read_points()
    scenario = read_scenario()

    zoom = zoom_crop(view, points)
    canvas = Image.new("RGBA", (1800, 1080), (235, 241, 248, 255))
    draw = ImageDraw.Draw(canvas)

    header_font = load_font(44, bold=True)
    sub_font = load_font(24)
    draw.text((74, 48), "Module 1 Digital Twin Presentation Board", fill=(20, 32, 46), font=header_font)
    draw.text(
        (74, 104),
        "Prediction-driven dispatch results bridged from Python into the actual Unity city scene.",
        fill=(74, 88, 106),
        font=sub_font,
    )

    left_card = Image.new("RGBA", (1180, 860), (255, 255, 255, 245))
    overview = fit_image(annotated, 1120, 700)
    overview_y = 30
    left_card.alpha_composite(overview, ((left_card.width - overview.width) // 2, overview_y))
    lc_draw = ImageDraw.Draw(left_card)
    lc_draw.text(
        (32, overview_y + overview.height + 28),
        "Overview: top-3 predicted dispatch hotspots over the Unity city scene",
        fill=(64, 80, 98),
        font=load_font(22),
    )

    right_card = Image.new("RGBA", (460, 860), (23, 37, 57, 245))
    rc_draw = ImageDraw.Draw(right_card)
    rc_draw.text((28, 30), "Dispatch Snapshot", fill=(248, 250, 252), font=load_font(34, bold=True))
    rc_draw.text((28, 76), "Current best presentation asset", fill=(187, 198, 212), font=load_font(20))

    zoom_title_font = load_font(24, bold=True)
    zoom_box = fit_image(zoom, 404, 220)
    rc_draw.text((28, 124), "Zoomed Hotspot Cluster", fill=(248, 250, 252), font=zoom_title_font)
    zoom_x = 28 + (404 - zoom_box.width) // 2
    right_card.alpha_composite(zoom_box, (zoom_x, 162))
    rc_draw.rounded_rectangle((zoom_x - 4, 158, zoom_x + zoom_box.width + 4, 162 + zoom_box.height + 4), radius=18, outline=(255, 255, 255), width=2)

    build_hotspot_cards(rc_draw, scenario, 28, 420, 404)

    add_shadow(canvas, left_card, 62, 154, blur_radius=18)
    add_shadow(canvas, right_card, 1272, 154, blur_radius=18)

    canvas.save(OUTPUT_IMAGE)
    print(f"Saved presentation board: {OUTPUT_IMAGE}")


if __name__ == "__main__":
    main()

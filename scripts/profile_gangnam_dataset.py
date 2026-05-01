from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET = ROOT_DIR / "data" / "processed" / "gangnam_ultimate_dataset.csv"
OUTPUT = ROOT_DIR / "outputs" / "data_profile" / "gangnam_ultimate_profile.json"


def clean_key(row: dict[str, str], key: str) -> str:
    return row.get(key, row.get("\ufeff" + key, "")).strip()


def main() -> None:
    if not DATASET.exists():
        raise SystemExit(f"Missing dataset: {DATASET}")

    row_count = 0
    date_values: list[str] = []
    hour_values: Counter[str] = Counter()
    dong_names: Counter[str] = Counter()
    codes_by_name: dict[str, set[str]] = defaultdict(set)

    with DATASET.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        for row in reader:
            row_count += 1
            date = clean_key(row, "기준일ID")
            hour = clean_key(row, "시간대구분")
            dong_code = clean_key(row, "행정동코드")
            dong_name = clean_key(row, "행정동명")

            if date:
                date_values.append(date)
            if hour:
                hour_values[hour] += 1
            if dong_name:
                dong_names[dong_name] += 1
            if dong_name and dong_code:
                codes_by_name[dong_name].add(dong_code)

    duplicate_code_names = {
        name: sorted(codes)
        for name, codes in sorted(codes_by_name.items())
        if len(codes) > 1
    }

    profile = {
        "dataset": str(DATASET.relative_to(ROOT_DIR)),
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "date_min": min(date_values) if date_values else None,
        "date_max": max(date_values) if date_values else None,
        "hour_values": sorted(hour_values),
        "dong_count": len(dong_names),
        "dong_names": sorted(dong_names),
        "duplicate_code_names": duplicate_code_names,
        "notes": [
            "This is a Gangnam dong-hour feature table.",
            "It does not contain exact taxi pickup coordinates or exact pickup counts.",
            "Use it for relative demand heatmap prediction.",
        ],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    print(f"saved: {OUTPUT}")


if __name__ == "__main__":
    main()


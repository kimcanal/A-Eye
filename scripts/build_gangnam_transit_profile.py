from __future__ import annotations

import argparse
import csv
import io
import json
from calendar import monthrange
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
RAW_DIR = WORKSPACE_DIR / "a-eye-raw-data" / "seoul-raw"
TARGET_DONGS_JSON = ROOT_DIR / "data" / "target_gangnam_dongs.json"
OUTPUT_DIR = ROOT_DIR / "data" / "processed" / "transit"
REPORT_PATH = ROOT_DIR / "docs" / "GANGNAM_TRANSIT_COLLECTION.md"

HOURS = [f"{hour:02d}" for hour in range(24)]

STATION_TO_DONG = {
    "강남": "역삼1동",
    "역삼": "역삼1동",
    "언주": "논현2동",
    "신논현": "논현1동",
    "논현": "논현1동",
    "학동": "논현2동",
    "강남구청": "논현2동",
    "선릉": "삼성2동",
    "선정릉": "삼성2동",
    "삼성중앙": "삼성2동",
    "삼성": "삼성1동",
    "봉은사": "삼성1동",
    "청담": "청담동",
    "압구정": "압구정동",
    "압구정로데오": "압구정동",
    "신사": "신사동",
    "한티": "대치4동",
}


def load_target_dongs() -> tuple[list[dict[str, object]], dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    data = json.loads(TARGET_DONGS_JSON.read_text(encoding="utf-8"))
    dongs = data["dongs"]
    by_code = {dong["transit_dong_code"]: dong for dong in dongs}
    by_name = {dong["dong_name"]: dong for dong in dongs}
    return dongs, by_code, by_name


def number(value: str | None) -> int:
    if value is None:
        return 0
    value = value.strip().replace(",", "")
    if not value:
        return 0
    return int(float(value))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_od_hourly(month: str, dongs: list[dict[str, object]], by_code: dict[str, dict[str, object]]) -> dict[str, object]:
    zip_path = RAW_DIR / "transit-od-hourly-dong" / f"tpss_emd_odh_{month}.zip"
    if not zip_path.exists():
        raise SystemExit(f"Missing OD hourly zip: {zip_path}")

    aggregates: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: {"inbound": 0, "outbound": 0, "internal": 0}
    )
    dates: set[str] = set()
    raw_rows = 0
    matched_rows = 0

    with ZipFile(zip_path) as z:
        for member in sorted(name for name in z.namelist() if name.endswith(".csv")):
            with z.open(member) as binary:
                text = io.TextIOWrapper(binary, encoding="cp949", newline="")
                reader = csv.DictReader(text)
                for row in reader:
                    raw_rows += 1
                    date = row["기준_날짜"]
                    start_code = row["시작_행정동_ID"]
                    end_code = row["종료_행정동_ID"]
                    start_dong = by_code.get(start_code)
                    end_dong = by_code.get(end_code)
                    if not start_dong and not end_dong:
                        continue
                    matched_rows += 1
                    dates.add(date)
                    for hour in HOURS:
                        passengers = number(row.get(f"승객_수_{hour}"))
                        if passengers <= 0:
                            continue
                        if start_dong:
                            key = (date, hour, str(start_dong["dong_name"]))
                            aggregates[key]["outbound"] += passengers
                        if end_dong:
                            key = (date, hour, str(end_dong["dong_name"]))
                            aggregates[key]["inbound"] += passengers
                        if start_dong and end_dong:
                            key = (date, hour, str(start_dong["dong_name"]))
                            aggregates[key]["internal"] += passengers

    if not dates:
        raise SystemExit(f"No matched target dong rows in {zip_path}")

    hourly_rows: list[dict[str, object]] = []
    for date in sorted(dates):
        for hour in HOURS:
            for dong in dongs:
                key = (date, hour, str(dong["dong_name"]))
                values = aggregates[key]
                inbound = values["inbound"]
                outbound = values["outbound"]
                internal = values["internal"]
                hourly_rows.append(
                    {
                        "service_date": date,
                        "service_hour": int(hour),
                        "dong_name": dong["dong_name"],
                        "transit_dong_code": dong["transit_dong_code"],
                        "included_in_3d_map": int(bool(dong["included_in_3d_map"])),
                        "transit_inbound": inbound,
                        "transit_outbound": outbound,
                        "transit_internal": internal,
                        "transit_pressure": inbound + outbound - internal,
                    }
                )

    hourly_path = OUTPUT_DIR / f"gangnam_transit_od_hourly_{month}.csv"
    write_csv(
        hourly_path,
        [
            "service_date",
            "service_hour",
            "dong_name",
            "transit_dong_code",
            "included_in_3d_map",
            "transit_inbound",
            "transit_outbound",
            "transit_internal",
            "transit_pressure",
        ],
        hourly_rows,
    )

    days = len(dates)
    summary_acc: dict[tuple[str, int], dict[str, float]] = defaultdict(
        lambda: {"inbound": 0.0, "outbound": 0.0, "internal": 0.0, "pressure": 0.0}
    )
    for row in hourly_rows:
        key = (str(row["dong_name"]), int(row["service_hour"]))
        summary_acc[key]["inbound"] += int(row["transit_inbound"])
        summary_acc[key]["outbound"] += int(row["transit_outbound"])
        summary_acc[key]["internal"] += int(row["transit_internal"])
        summary_acc[key]["pressure"] += int(row["transit_pressure"])

    summary_rows: list[dict[str, object]] = []
    for dong in dongs:
        for hour in range(24):
            values = summary_acc[(str(dong["dong_name"]), hour)]
            summary_rows.append(
                {
                    "month": month,
                    "service_hour": hour,
                    "dong_name": dong["dong_name"],
                    "transit_dong_code": dong["transit_dong_code"],
                    "included_in_3d_map": int(bool(dong["included_in_3d_map"])),
                    "avg_inbound": round(values["inbound"] / days, 3),
                    "avg_outbound": round(values["outbound"] / days, 3),
                    "avg_internal": round(values["internal"] / days, 3),
                    "avg_transit_pressure": round(values["pressure"] / days, 3),
                }
            )

    summary_path = OUTPUT_DIR / f"gangnam_transit_od_hourly_summary_{month}.csv"
    write_csv(
        summary_path,
        [
            "month",
            "service_hour",
            "dong_name",
            "transit_dong_code",
            "included_in_3d_map",
            "avg_inbound",
            "avg_outbound",
            "avg_internal",
            "avg_transit_pressure",
        ],
        summary_rows,
    )

    peak_by_dong: list[dict[str, object]] = []
    for dong in dongs:
        dong_rows = [row for row in summary_rows if row["dong_name"] == dong["dong_name"]]
        best = max(dong_rows, key=lambda row: float(row["avg_transit_pressure"]))
        peak_by_dong.append(
            {
                "month": month,
                "dong_name": dong["dong_name"],
                "peak_hour": best["service_hour"],
                "avg_transit_pressure": best["avg_transit_pressure"],
                "avg_inbound": best["avg_inbound"],
                "avg_outbound": best["avg_outbound"],
                "included_in_3d_map": best["included_in_3d_map"],
            }
        )

    peak_by_dong.sort(key=lambda row: float(row["avg_transit_pressure"]), reverse=True)
    peak_by_dong_path = OUTPUT_DIR / f"gangnam_transit_peak_by_dong_{month}.csv"
    write_csv(
        peak_by_dong_path,
        [
            "month",
            "dong_name",
            "peak_hour",
            "avg_transit_pressure",
            "avg_inbound",
            "avg_outbound",
            "included_in_3d_map",
        ],
        peak_by_dong,
    )

    hour_acc: dict[int, float] = defaultdict(float)
    for row in summary_rows:
        hour_acc[int(row["service_hour"])] += float(row["avg_transit_pressure"])
    peak_hours = [
        {"month": month, "service_hour": hour, "avg_micro_area_pressure": round(value, 3)}
        for hour, value in sorted(hour_acc.items(), key=lambda item: item[1], reverse=True)
    ]
    for index, row in enumerate(peak_hours, start=1):
        row["rank"] = index

    peak_hours_path = OUTPUT_DIR / f"gangnam_transit_peak_hours_{month}.csv"
    write_csv(
        peak_hours_path,
        ["month", "service_hour", "avg_micro_area_pressure", "rank"],
        peak_hours,
    )

    return {
        "zip_path": str(zip_path.relative_to(WORKSPACE_DIR)),
        "raw_rows": raw_rows,
        "matched_rows": matched_rows,
        "days": days,
        "hourly_path": str(hourly_path.relative_to(ROOT_DIR)),
        "summary_path": str(summary_path.relative_to(ROOT_DIR)),
        "peak_by_dong_path": str(peak_by_dong_path.relative_to(ROOT_DIR)),
        "peak_hours_path": str(peak_hours_path.relative_to(ROOT_DIR)),
        "top_peak_hours": peak_hours[:5],
        "top_peak_dongs": peak_by_dong[:5],
    }


def build_subway_station_profile(month: str, by_name: dict[str, dict[str, object]]) -> dict[str, object]:
    json_path = RAW_DIR / "subway-time-station" / f"CardSubwayTime_{month}.json"
    if not json_path.exists():
        raise SystemExit(f"Missing subway time JSON: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    days = monthrange(int(month[:4]), int(month[4:]))[1]

    station_rows: list[dict[str, object]] = []
    for row in rows:
        station = str(row.get("STTN", ""))
        dong_name = STATION_TO_DONG.get(station)
        if not dong_name or dong_name not in by_name:
            continue
        dong = by_name[dong_name]
        for hour in range(24):
            get_on = number(str(row.get(f"HR_{hour}_GET_ON_NOPE", "0")))
            get_off = number(str(row.get(f"HR_{hour}_GET_OFF_NOPE", "0")))
            station_rows.append(
                {
                    "month": month,
                    "station_name": station,
                    "line_name": row.get("SBWY_ROUT_LN_NM", ""),
                    "dong_name": dong_name,
                    "transit_dong_code": dong["transit_dong_code"],
                    "included_in_3d_map": int(bool(dong["included_in_3d_map"])),
                    "service_hour": hour,
                    "monthly_get_on": get_on,
                    "monthly_get_off": get_off,
                    "daily_avg_get_on": round(get_on / days, 3),
                    "daily_avg_get_off": round(get_off / days, 3),
                    "daily_avg_station_pressure": round((get_on + get_off) / days, 3),
                }
            )

    station_path = OUTPUT_DIR / f"gangnam_subway_station_hourly_{month}.csv"
    write_csv(
        station_path,
        [
            "month",
            "station_name",
            "line_name",
            "dong_name",
            "transit_dong_code",
            "included_in_3d_map",
            "service_hour",
            "monthly_get_on",
            "monthly_get_off",
            "daily_avg_get_on",
            "daily_avg_get_off",
            "daily_avg_station_pressure",
        ],
        station_rows,
    )

    dong_hour_acc: dict[tuple[str, int], float] = defaultdict(float)
    for row in station_rows:
        dong_hour_acc[(str(row["dong_name"]), int(row["service_hour"]))] += float(
            row["daily_avg_station_pressure"]
        )

    summary_rows: list[dict[str, object]] = []
    for dong_name, dong in by_name.items():
        for hour in range(24):
            summary_rows.append(
                {
                    "month": month,
                    "dong_name": dong_name,
                    "transit_dong_code": dong["transit_dong_code"],
                    "included_in_3d_map": int(bool(dong["included_in_3d_map"])),
                    "service_hour": hour,
                    "daily_avg_subway_pressure": round(dong_hour_acc[(dong_name, hour)], 3),
                }
            )

    summary_path = OUTPUT_DIR / f"gangnam_subway_dong_hourly_summary_{month}.csv"
    write_csv(
        summary_path,
        [
            "month",
            "dong_name",
            "transit_dong_code",
            "included_in_3d_map",
            "service_hour",
            "daily_avg_subway_pressure",
        ],
        summary_rows,
    )

    station_totals: dict[tuple[str, str], float] = defaultdict(float)
    for row in station_rows:
        station_totals[(str(row["station_name"]), str(row["dong_name"]))] += float(
            row["daily_avg_station_pressure"]
        )
    top_stations = [
        {
            "station_name": station,
            "dong_name": dong_name,
            "daily_avg_station_pressure": round(value, 3),
        }
        for (station, dong_name), value in sorted(
            station_totals.items(), key=lambda item: item[1], reverse=True
        )
    ]

    return {
        "json_path": str(json_path.relative_to(WORKSPACE_DIR)),
        "source_rows": len(rows),
        "matched_station_hour_rows": len(station_rows),
        "station_path": str(station_path.relative_to(ROOT_DIR)),
        "summary_path": str(summary_path.relative_to(ROOT_DIR)),
        "top_stations": top_stations[:10],
    }


def write_report(month: str, od_summary: dict[str, object], subway_summary: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gangnam Transit Collection",
        "",
        f"Month: `{month}`",
        "",
        "## Decision",
        "",
        "Use Gangnam/Yeoksam-area Seoul public-transport data first. The NYC TLC",
        "dataset remains useful for real 5-minute taxi-label structure, but the",
        "Gangnam transit profile is the stronger local demand proxy for presentation.",
        "",
        "## Target Dongs",
        "",
        "- 신사동",
        "- 논현1동",
        "- 논현2동",
        "- 삼성1동",
        "- 삼성2동",
        "- 대치4동",
        "- 역삼1동",
        "- 역삼2동",
        "- 압구정동",
        "- 청담동",
        "",
        "`압구정동` is present in `gangnam_ultimate_dataset.csv`, while the current",
        "`__yeoksam_taxi` 3D map uses the other 9 dongs.",
        "",
        "## Generated Artifacts",
        "",
        f"- `{od_summary['hourly_path']}`",
        f"- `{od_summary['summary_path']}`",
        f"- `{od_summary['peak_by_dong_path']}`",
        f"- `{od_summary['peak_hours_path']}`",
        f"- `{subway_summary['station_path']}`",
        f"- `{subway_summary['summary_path']}`",
        "",
        "## Top Micro-Area Transit Hours",
        "",
        "| Rank | Hour | Avg micro-area pressure |",
        "|---:|---:|---:|",
    ]
    for row in od_summary["top_peak_hours"]:
        lines.append(
            f"| {row['rank']} | {row['service_hour']} | {row['avg_micro_area_pressure']} |"
        )
    lines.extend(
        [
            "",
            "## Top Dong Peak Pressures",
            "",
            "| Dong | Peak hour | Avg pressure | Inbound | Outbound |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in od_summary["top_peak_dongs"]:
        lines.append(
            f"| {row['dong_name']} | {row['peak_hour']} | {row['avg_transit_pressure']} | {row['avg_inbound']} | {row['avg_outbound']} |"
        )
    lines.extend(
        [
            "",
            "## Top Subway Stations",
            "",
            "| Station | Dong | Daily avg station pressure |",
            "|---|---|---:|",
        ]
    )
    for row in subway_summary["top_stations"][:8]:
        lines.append(
            f"| {row['station_name']} | {row['dong_name']} | {row['daily_avg_station_pressure']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is not taxi demand ground truth. It is a local movement-pressure proxy:",
            "",
            "- high inbound/outbound public-transport flow indicates people movement",
            "- taxi demand often rises around high movement pressure, bad weather, and low road speed",
            "- combine this with `gangnam_ultimate_dataset.csv` for relative demand scoring",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", default="202603")
    args = parser.parse_args()

    dongs, by_code, by_name = load_target_dongs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    od_summary = build_od_hourly(args.month, dongs, by_code)
    subway_summary = build_subway_station_profile(args.month, by_name)
    write_report(args.month, od_summary, subway_summary)
    print(json.dumps({"od": od_summary, "subway": subway_summary}, ensure_ascii=False, indent=2))
    print(f"saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()

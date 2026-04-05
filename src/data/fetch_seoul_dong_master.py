from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pandas as pd


API_BASE = "http://openAPI.seoul.go.kr:8088"
SERVICE_NAME = "districtEmd"
DEFAULT_KEY = "sample"
PAGE_SIZE = 1000
RAW_OUTPUT_DIR = Path("data/seoul_public/raw")
DONG_MASTER_CSV = Path("data/seoul_public/dong_master.csv")


def build_url(api_key: str, start: int, end: int) -> str:
    return f"{API_BASE}/{api_key}/json/{SERVICE_NAME}/{start}/{end}/"


def fetch_json(url: str) -> dict:
    try:
        with urlopen(url, timeout=60) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:  # pragma: no cover
        raise SystemExit(f"HTTP error while fetching Seoul API: {exc}") from exc
    except URLError as exc:  # pragma: no cover
        raise SystemExit(f"Network error while fetching Seoul API: {exc}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        code_match = re.search(r"<CODE>(.*?)</CODE>", body)
        message_match = re.search(r"<MESSAGE><!\[CDATA\[(.*?)\]\]></MESSAGE>", body, flags=re.S)
        if code_match or message_match:
            code = code_match.group(1) if code_match else "UNKNOWN"
            message = message_match.group(1).strip() if message_match else "Unknown Seoul API error"
            raise SystemExit(f"Seoul API error [{code}]: {message}")

        preview = body[:200].replace("\n", " ")
        raise SystemExit(f"Unexpected non-JSON response from Seoul API: {preview}")


def fetch_rows(api_key: str) -> list[dict]:
    all_rows: list[dict] = []
    start = 1

    while True:
        end = 5 if api_key == DEFAULT_KEY else start + PAGE_SIZE - 1
        payload = fetch_json(build_url(api_key, start, end))

        if "RESULT" in payload:
            raise SystemExit(payload["RESULT"].get("MESSAGE", "Unknown API error"))

        root = payload.get(SERVICE_NAME)
        if not root:
            raise SystemExit("Unexpected Seoul API response: missing service root")

        result = root.get("RESULT", {})
        if result.get("CODE") != "INFO-000":
            raise SystemExit(result.get("MESSAGE", "Seoul API returned a non-success result"))

        rows = root.get("row", [])
        all_rows.extend(rows)

        if api_key == DEFAULT_KEY or not rows or len(rows) < PAGE_SIZE:
            break

        start += PAGE_SIZE

    return all_rows


def build_master_frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows).copy()
    if df.empty:
        raise SystemExit("No rows were returned for districtEmd.")

    renamed = df.rename(
        columns={
            "DONG_ID": "zone_id",
            "DONG_NM": "zone_name",
            "CGG_NM": "gu_name",
            "CTPV_NM": "city_name",
        }
    )
    renamed["zone_id"] = renamed["zone_id"].astype(str)
    renamed["full_zone_name"] = renamed["gu_name"].fillna("") + " " + renamed["zone_name"].fillna("")
    renamed["full_zone_name"] = renamed["full_zone_name"].str.strip()
    return renamed[["zone_id", "zone_name", "gu_name", "city_name", "full_zone_name"]].drop_duplicates()


def fetch_and_save(output_csv: Path = DONG_MASTER_CSV) -> Path:
    api_key = os.environ.get("SEOUL_OPEN_API_KEY", DEFAULT_KEY)
    key_type = "sample" if api_key == DEFAULT_KEY else "custom"

    rows = fetch_rows(api_key)
    master_df = build_master_frame(rows)

    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    raw_output_path = RAW_OUTPUT_DIR / f"{SERVICE_NAME}_{key_type}.json"
    raw_output_path.write_text(
        json.dumps(
            {
                "service": SERVICE_NAME,
                "api_key_type": key_type,
                "row_count": len(rows),
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    master_df.to_csv(output_csv, index=False)

    print(f"saved: {raw_output_path}")
    print(f"saved: {output_csv}")
    print(f"rows: {len(master_df)}")
    return output_csv


def ensure_dong_master_csv(output_csv: Path = DONG_MASTER_CSV) -> Path:
    if output_csv.exists():
        return output_csv
    return fetch_and_save(output_csv)


def main() -> None:
    fetch_and_save()


if __name__ == "__main__":
    main()

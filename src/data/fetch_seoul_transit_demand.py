from __future__ import annotations

import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


API_BASE = "http://openAPI.seoul.go.kr:8088"
SERVICE_NAME = "tpssPassengerCnt"
DEFAULT_KEY = "sample"
PAGE_SIZE = 1000
PROGRESS_INTERVAL = 20


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


def main() -> None:
    api_key = os.environ.get("SEOUL_OPEN_API_KEY", DEFAULT_KEY)
    output_dir = Path("data/seoul_public/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    key_type = "sample" if api_key == DEFAULT_KEY else "custom"

    all_rows: list[dict] = []
    total_count = None
    start = 1
    page = 0

    print(f"fetching Seoul API service={SERVICE_NAME} key_type={key_type}")

    while True:
        if api_key == DEFAULT_KEY:
            end = 5
        else:
            end = start + PAGE_SIZE - 1

        payload = fetch_json(build_url(api_key, start, end))
        page += 1

        if "RESULT" in payload:
            raise SystemExit(payload["RESULT"].get("MESSAGE", "Unknown API error"))

        root = payload.get(SERVICE_NAME)
        if not root:
            raise SystemExit("Unexpected Seoul API response: missing service root")

        result = root.get("RESULT", {})
        if result.get("CODE") != "INFO-000":
            raise SystemExit(result.get("MESSAGE", "Seoul API returned a non-success result"))

        rows = root.get("row", [])
        total_count = int(root.get("list_total_count", len(rows)))
        all_rows.extend(rows)

        if page == 1 or page % PROGRESS_INTERVAL == 0 or len(all_rows) >= total_count:
            print(f"page={page} rows_fetched={len(all_rows)} total_count={total_count}")

        if api_key == DEFAULT_KEY or not rows or len(all_rows) >= total_count:
            break

        start += PAGE_SIZE

    output_path = output_dir / f"{SERVICE_NAME}_{key_type}.json"
    output_path.write_text(
        json.dumps(
            {
                "service": SERVICE_NAME,
                "api_key_type": key_type,
                "row_count": len(all_rows),
                "list_total_count": total_count,
                "rows": all_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"saved: {output_path}")
    print(f"rows: {len(all_rows)}")
    print(f"total_count: {total_count}")
    if api_key == DEFAULT_KEY:
        print("note: sample API key returns at most 5 rows; set SEOUL_OPEN_API_KEY for full data.")


if __name__ == "__main__":
    main()

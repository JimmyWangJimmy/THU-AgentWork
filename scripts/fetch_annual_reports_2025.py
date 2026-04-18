#!/usr/bin/env python3
"""Fetch 2025 A-share annual report PDFs from CNINFO.

Output:
1) reports_raw/<stock_code>_<company_name>/2025/<announcement_id>.pdf
2) reports_raw/download_manifest_2025.csv
3) reports_raw/download_failures_2025.csv
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import html
import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode, urljoin
from urllib.request import ProxyHandler, Request, build_opener


API_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
SEARCH_REFERER = "https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/search"
DOWNLOAD_BASE_URL = "https://static.cninfo.com.cn/"

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": SEARCH_REFERER,
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

# Disable system proxy auto-discovery to avoid sporadic TLS handshake stalls.
HTTP_OPENER = build_opener(ProxyHandler({}))

INVALID_CHARS = re.compile(r'[\\/:*?"<>|]+')
EM_TAG = re.compile(r"</?em>")
REPORT_PATTERN = re.compile(r"(20\d{2})年年度报告")


@dataclass
class ReportRecord:
    sec_code: str
    sec_name: str
    announcement_id: str
    announcement_title: str
    announcement_time_ms: int
    announcement_time_iso: str
    adjunct_url: str
    source_url: str
    report_year: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch 2025 A-share annual report PDFs from CNINFO.")
    parser.add_argument("--start-date", default="2025-01-01", help="Query start date, format YYYY-MM-DD")
    parser.add_argument("--end-date", default="2026-12-31", help="Query end date, format YYYY-MM-DD")
    parser.add_argument("--out-dir", default="reports_raw", help="Output directory for PDF files and CSVs")
    parser.add_argument("--max-workers", type=int, default=4, help="Concurrent download workers")
    parser.add_argument("--retry", type=int, default=3, help="Retry count for query/download")
    parser.add_argument("--max-pages", type=int, default=0, help="Limit fetched pages for testing. 0 = all")
    parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout seconds")
    parser.add_argument(
        "--sec-prefixes",
        default="",
        help='Optional stock code prefixes, e.g. "000,001,002,300,600,601,603,688,920"',
    )
    parser.add_argument(
        "--manifest-suffix",
        default="",
        help='Optional suffix for output CSV names, e.g. "_000_300"',
    )
    return parser.parse_args()


def backoff_sleep(attempt: int) -> None:
    delay = (2 ** attempt) + random.uniform(0, 0.5)
    time.sleep(delay)


def post_json_with_retry(payload: Dict[str, str], retries: int, timeout: int) -> Dict:
    last_error: Optional[Exception] = None
    encoded = urlencode(payload).encode("utf-8")
    for attempt in range(retries + 1):
        try:
            req = Request(API_URL, data=encoded, headers=DEFAULT_HEADERS, method="POST")
            with HTTP_OPENER.open(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                return json.loads(body)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                backoff_sleep(attempt)
    raise RuntimeError(f"CNINFO query failed after {retries + 1} attempts: {last_error}") from last_error


def get_with_retry(url: str, retries: int, timeout: int) -> bytes:
    last_error: Optional[Exception] = None
    headers = {
        "User-Agent": DEFAULT_HEADERS["User-Agent"],
        "Referer": SEARCH_REFERER,
        "Accept": "application/pdf,*/*",
        "Connection": "close",
    }
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers=headers, method="GET")
            with HTTP_OPENER.open(req, timeout=timeout) as resp:
                content = resp.read()
                if not content:
                    raise RuntimeError("Empty content")
                return content
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                backoff_sleep(attempt)
    raise RuntimeError(f"Download failed after {retries + 1} attempts: {last_error}") from last_error


def strip_markup(text: str) -> str:
    no_tag = EM_TAG.sub("", text or "")
    return html.unescape(no_tag).strip()


def report_year_from_title(title: str) -> Optional[int]:
    m = REPORT_PATTERN.search(title)
    if not m:
        return None
    return int(m.group(1))


def is_target_2025_report(title: str) -> bool:
    cleaned = strip_markup(title)
    return "2025年年度报告" in cleaned and "摘要" not in cleaned


def sanitize_component(name: str) -> str:
    value = INVALID_CHARS.sub("_", name.strip())
    value = re.sub(r"\s+", "_", value)
    value = value.strip("._")
    return value or "UNKNOWN"


def to_iso_time(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def fetch_candidate_announcements(
    start_date: str,
    end_date: str,
    retries: int,
    timeout: int,
    max_pages: int,
) -> List[Dict]:
    page_num = 1
    page_size = 30
    all_announcements: List[Dict] = []
    total_pages = None

    while True:
        payload = {
            "pageNum": str(page_num),
            "pageSize": str(page_size),
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "searchkey": "2025年年度报告",
            "secid": "",
            "category": "category_ndbg_szsh",
            "seDate": f"{start_date}~{end_date}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
        data = post_json_with_retry(payload, retries=retries, timeout=timeout)
        announcements = data.get("announcements") or []
        total_pages = int(data.get("totalpages") or 0)
        all_announcements.extend(announcements)

        if page_num == 1 or page_num % 20 == 0:
            total_text = str(total_pages) if total_pages else "?"
            print(f"[fetch] page {page_num}/{total_text}, cumulative={len(all_announcements)}")

        if not announcements:
            break
        if max_pages > 0 and page_num >= max_pages:
            break
        if total_pages and page_num >= total_pages:
            break

        page_num += 1

    return all_announcements


def normalize_records(candidates: Iterable[Dict]) -> List[ReportRecord]:
    records: List[ReportRecord] = []
    for item in candidates:
        title = strip_markup(item.get("announcementTitle", ""))
        if not is_target_2025_report(title):
            continue
        if item.get("adjunctType", "").upper() != "PDF":
            continue

        report_year = report_year_from_title(title)
        if report_year != 2025:
            continue

        sec_code = str(item.get("secCode", "")).strip()
        sec_name = str(item.get("secName", "")).strip()
        announcement_id = str(item.get("announcementId", "")).strip()
        adjunct_url = str(item.get("adjunctUrl", "")).strip()
        announcement_time_ms = int(item.get("announcementTime") or 0)

        if not sec_code or not announcement_id or not adjunct_url or announcement_time_ms <= 0:
            continue

        records.append(
            ReportRecord(
                sec_code=sec_code,
                sec_name=sec_name or "UNKNOWN",
                announcement_id=announcement_id,
                announcement_title=title,
                announcement_time_ms=announcement_time_ms,
                announcement_time_iso=to_iso_time(announcement_time_ms),
                adjunct_url=adjunct_url,
                source_url=urljoin(DOWNLOAD_BASE_URL, adjunct_url),
                report_year=report_year,
            )
        )
    return records


def parse_sec_prefixes(raw: str) -> Tuple[str, ...]:
    if not raw:
        return ()
    prefixes = [part.strip() for part in raw.split(",")]
    return tuple(part for part in prefixes if part)


def filter_by_sec_prefixes(records: Iterable[ReportRecord], prefixes: Tuple[str, ...]) -> List[ReportRecord]:
    if not prefixes:
        return list(records)
    return [rec for rec in records if rec.sec_code.startswith(prefixes)]


def dedupe_latest(records: Iterable[ReportRecord]) -> List[ReportRecord]:
    latest: Dict[Tuple[str, int], ReportRecord] = {}
    for rec in records:
        key = (rec.sec_code, rec.report_year)
        current = latest.get(key)
        if current is None:
            latest[key] = rec
            continue
        if rec.announcement_time_ms > current.announcement_time_ms:
            latest[key] = rec
        elif rec.announcement_time_ms == current.announcement_time_ms and rec.announcement_id > current.announcement_id:
            latest[key] = rec
    return sorted(latest.values(), key=lambda x: (x.sec_code, x.announcement_id))


def build_target_path(out_dir: Path, rec: ReportRecord) -> Path:
    company_dir_name = f"{rec.sec_code}_{sanitize_component(rec.sec_name)}"
    return out_dir / company_dir_name / "2025" / f"{rec.announcement_id}.pdf"


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def download_one(rec: ReportRecord, out_dir: Path, retries: int, timeout: int) -> Tuple[bool, Dict[str, str]]:
    target_path = build_target_path(out_dir, rec)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists() and target_path.stat().st_size > 0:
        return True, {
            "sec_code": rec.sec_code,
            "sec_name": rec.sec_name,
            "announcement_title": rec.announcement_title,
            "announcement_time": rec.announcement_time_iso,
            "announcement_id": rec.announcement_id,
            "local_path": str(target_path),
            "source_url": rec.source_url,
        }

    try:
        content = get_with_retry(rec.source_url, retries=retries, timeout=timeout)
        tmp_path = target_path.with_suffix(".tmp")
        with tmp_path.open("wb") as f:
            f.write(content)
        tmp_path.replace(target_path)
        return True, {
            "sec_code": rec.sec_code,
            "sec_name": rec.sec_name,
            "announcement_title": rec.announcement_title,
            "announcement_time": rec.announcement_time_iso,
            "announcement_id": rec.announcement_id,
            "local_path": str(target_path),
            "source_url": rec.source_url,
        }
    except Exception as exc:  # noqa: BLE001
        return False, {
            "announcement_id": rec.announcement_id,
            "sec_code": rec.sec_code,
            "sec_name": rec.sec_name,
            "announcement_title": rec.announcement_title,
            "reason": str(exc),
            "retries": str(retries),
        }


def download_reports(
    records: List[ReportRecord],
    out_dir: Path,
    workers: int,
    retries: int,
    timeout: int,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    manifest_rows: List[Dict[str, str]] = []
    failure_rows: List[Dict[str, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_map = {
            executor.submit(download_one, rec, out_dir, retries, timeout): rec for rec in records
        }
        for future in concurrent.futures.as_completed(future_map):
            ok, row = future.result()
            if ok:
                manifest_rows.append(row)
            else:
                failure_rows.append(row)

    manifest_rows.sort(key=lambda x: (x["sec_code"], x["announcement_id"]))
    failure_rows.sort(key=lambda x: (x["sec_code"], x["announcement_id"]))
    return manifest_rows, failure_rows


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("== 2025 A-share annual report fetch started ==")
    print(f"Date range: {args.start_date} ~ {args.end_date}")
    print(f"Output dir: {out_dir.resolve()}")

    candidates = fetch_candidate_announcements(
        start_date=args.start_date,
        end_date=args.end_date,
        retries=args.retry,
        timeout=args.timeout,
        max_pages=args.max_pages,
    )
    filtered = normalize_records(candidates)
    sec_prefixes = parse_sec_prefixes(args.sec_prefixes)
    filtered_by_prefix = filter_by_sec_prefixes(filtered, sec_prefixes)
    deduped = dedupe_latest(filtered_by_prefix)

    manifest_rows, failure_rows = download_reports(
        records=deduped,
        out_dir=out_dir,
        workers=args.max_workers,
        retries=args.retry,
        timeout=args.timeout,
    )

    manifest_suffix = args.manifest_suffix or ""
    manifest_path = out_dir / f"download_manifest_2025{manifest_suffix}.csv"
    failures_path = out_dir / f"download_failures_2025{manifest_suffix}.csv"

    write_csv(
        manifest_path,
        fieldnames=[
            "sec_code",
            "sec_name",
            "announcement_title",
            "announcement_time",
            "announcement_id",
            "local_path",
            "source_url",
        ],
        rows=manifest_rows,
    )
    write_csv(
        failures_path,
        fieldnames=[
            "announcement_id",
            "sec_code",
            "sec_name",
            "announcement_title",
            "reason",
            "retries",
        ],
        rows=failure_rows,
    )

    print("== Summary ==")
    print(f"Candidates fetched: {len(candidates)}")
    print(f"Filtered (2025 full annual reports): {len(filtered)}")
    if sec_prefixes:
        print(f"After sec-prefix filter ({','.join(sec_prefixes)}): {len(filtered_by_prefix)}")
    print(f"Deduped (latest by secCode+year): {len(deduped)}")
    print(f"Download success: {len(manifest_rows)}")
    print(f"Download failed: {len(failure_rows)}")
    print(f"Manifest: {manifest_path.resolve()}")
    print(f"Failures: {failures_path.resolve()}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Restructure reports_raw into sharded subdirectories and rewrite manifest paths."""

from __future__ import annotations

import csv
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_RAW = REPO_ROOT / "reports_raw"
COMPANIES_DIR = REPORTS_RAW / "companies"
MANIFESTS_DIR = REPORTS_RAW / "manifests"
FAILURES_DIR = REPORTS_RAW / "failures"
INVALID_CHARS = re.compile(r'[\\/:*?"<>|]+')

SHARD_LABELS = {
    "000": "000_sz_main",
    "001": "001_sz_main",
    "002": "002_sz_main",
    "003": "003_sz_main",
    "200": "200_sz_b",
    "201": "201_sz_b",
    "300": "300_chinext",
    "301": "301_chinext",
    "600": "600_sh_main",
    "601": "601_sh_main",
    "603": "603_sh_main",
    "605": "605_sh_main",
    "688": "688_star",
    "689": "689_star",
    "900": "900_sh_b",
    "920": "920_bse",
}


def shard_dir_for_name(name: str) -> str:
    prefix = name[:3]
    return SHARD_LABELS.get(prefix, f"{prefix}_other")


def sanitize_component(name: str) -> str:
    value = INVALID_CHARS.sub("_", name.strip())
    value = re.sub(r"\s+", "_", value)
    value = value.strip("._")
    return value or "UNKNOWN"


def move_company_dirs() -> int:
    moved = 0
    COMPANIES_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(REPORTS_RAW.iterdir()):
        if not path.is_dir():
            continue
        if path.name in {"companies", "manifests", "failures", "logs"}:
            continue
        if len(path.name) < 4 or not path.name[:3].isdigit() or "_" not in path.name:
            continue
        target = COMPANIES_DIR / shard_dir_for_name(path.name) / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        path.rename(target)
        moved += 1
    return moved


def move_csvs() -> tuple[int, int]:
    manifest_count = 0
    failure_count = 0
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    FAILURES_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(REPORTS_RAW.glob("download_manifest_2025*.csv")):
        target = MANIFESTS_DIR / path.name
        if path.resolve() != target.resolve():
            path.rename(target)
        manifest_count += 1

    for path in sorted(REPORTS_RAW.glob("download_failures_2025*.csv")):
        target = FAILURES_DIR / path.name
        if path.resolve() != target.resolve():
            path.rename(target)
        failure_count += 1

    return manifest_count, failure_count


def rewrite_manifest_local_paths() -> int:
    rewritten = 0
    for manifest_path in sorted(MANIFESTS_DIR.glob("download_manifest_2025*.csv")):
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
            fieldnames = list(rows[0].keys()) if rows else [
                "sec_code",
                "sec_name",
                "announcement_title",
                "announcement_time",
                "announcement_id",
                "local_path",
                "source_url",
            ]

        changed = False
        for row in rows:
            sec_code = row.get("sec_code", "").strip()
            sec_name = row.get("sec_name", "").strip()
            announcement_id = row.get("announcement_id", "").strip()
            if not sec_code or not announcement_id:
                continue
            company_dir = f"{sec_code}_{sanitize_component(sec_name or 'UNKNOWN')}"
            expected_path = str(
                Path("reports_raw")
                / "companies"
                / shard_dir_for_name(company_dir)
                / company_dir
                / "2025"
                / f"{announcement_id}.pdf"
            )
            if row.get("local_path") != expected_path:
                row["local_path"] = expected_path
                changed = True

        if changed:
            with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            rewritten += 1
    return rewritten


def main() -> None:
    moved = move_company_dirs()
    manifest_count, failure_count = move_csvs()
    rewritten = rewrite_manifest_local_paths()

    print(f"Moved company directories: {moved}")
    print(f"Manifest CSV files under reports_raw/manifests: {manifest_count}")
    print(f"Failure CSV files under reports_raw/failures: {failure_count}")
    print(f"Manifest CSV files rewritten: {rewritten}")


if __name__ == "__main__":
    main()

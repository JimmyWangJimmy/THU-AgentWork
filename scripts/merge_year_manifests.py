#!/usr/bin/env python3
"""Merge per-window annual-report manifests into one deduped yearly manifest."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


MANIFEST_FIELDS = [
    "sec_code",
    "sec_name",
    "announcement_title",
    "announcement_time",
    "announcement_id",
    "local_path",
    "source_url",
]

FAILURE_FIELDS = [
    "announcement_id",
    "sec_code",
    "sec_name",
    "announcement_title",
    "reason",
    "retries",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge yearly annual-report manifests and failures.")
    parser.add_argument("--year", type=int, required=True, help="Report year, e.g. 2024")
    parser.add_argument("--out-dir", default="reports_raw", help="Base output directory")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def collect_window_manifests(manifests_dir: Path, year: int) -> list[Path]:
    return sorted(
        p
        for p in manifests_dir.glob(f"download_manifest_{year}_*.csv")
        if "full_refresh" not in p.name
    )


def collect_window_failures(failures_dir: Path, year: int) -> list[Path]:
    return sorted(
        p
        for p in failures_dir.glob(f"download_failures_{year}_*.csv")
        if "full_refresh" not in p.name
    )


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    manifests_dir = out_dir / "manifests"
    failures_dir = out_dir / "failures"

    manifest_files = collect_window_manifests(manifests_dir, args.year)
    failure_files = collect_window_failures(failures_dir, args.year)

    latest_by_company: dict[str, dict[str, str]] = {}
    success_ids: set[str] = set()

    for path in manifest_files:
        for row in read_csv_rows(path):
            announcement_id = row["announcement_id"]
            success_ids.add(announcement_id)
            sec_code = row["sec_code"]
            current = latest_by_company.get(sec_code)
            if current is None:
                latest_by_company[sec_code] = row
                continue
            lhs = parse_time(row["announcement_time"])
            rhs = parse_time(current["announcement_time"])
            if lhs > rhs or (lhs == rhs and row["announcement_id"] > current["announcement_id"]):
                latest_by_company[sec_code] = row

    merged_manifest_rows = sorted(
        latest_by_company.values(),
        key=lambda row: (row["sec_code"], row["announcement_id"]),
    )

    unresolved_failures: dict[str, dict[str, str]] = {}
    for path in failure_files:
        for row in read_csv_rows(path):
            announcement_id = row["announcement_id"]
            if announcement_id in success_ids:
                continue
            unresolved_failures[announcement_id] = row

    merged_failure_rows = sorted(
        unresolved_failures.values(),
        key=lambda row: (row["sec_code"], row["announcement_id"]),
    )

    manifest_out = manifests_dir / f"download_manifest_{args.year}_full_refresh.csv"
    failures_out = failures_dir / f"download_failures_{args.year}_full_refresh.csv"

    write_csv(manifest_out, MANIFEST_FIELDS, merged_manifest_rows)
    write_csv(failures_out, FAILURE_FIELDS, merged_failure_rows)

    print(f"Window manifests merged: {len(manifest_files)}")
    print(f"Window failures merged: {len(failure_files)}")
    print(f"Deduped manifest rows: {len(merged_manifest_rows)}")
    print(f"Unresolved failures: {len(merged_failure_rows)}")
    print(f"Manifest: {manifest_out}")
    print(f"Failures: {failures_out}")


if __name__ == "__main__":
    main()

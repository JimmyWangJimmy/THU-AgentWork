#!/usr/bin/env bash
#
# Usage:
#   bash scripts/run_parallel_fetch_2025.sh [REPORT_YEAR] [START_DATE] [END_DATE] [OUT_DIR] [RETRY] [TIMEOUT] [PAGE_DELAY]
# Example:
#   bash scripts/run_parallel_fetch_2025.sh 2024 2024-01-01 2025-12-31 reports_raw 3 25 0.5
#

set -u

REPORT_YEAR="${1:-2025}"
START_DATE="${2:-2025-01-01}"
END_DATE="${3:-2026-12-31}"
OUT_DIR="${4:-reports_raw}"
RETRY="${5:-3}"
TIMEOUT="${6:-25}"
PAGE_DELAY="${7:-0}"

PREFIXES=(000 001 002 300 600 601 603 688 920)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/fetch_annual_reports_2025.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
  echo "[error] fetch script not found: ${PY_SCRIPT}" >&2
  exit 2
fi

mkdir -p "${OUT_DIR}/logs"

pids=()
prefixes=()
logs=()

echo "[start] REPORT_YEAR=${REPORT_YEAR} START_DATE=${START_DATE} END_DATE=${END_DATE} OUT_DIR=${OUT_DIR} RETRY=${RETRY} TIMEOUT=${TIMEOUT} PAGE_DELAY=${PAGE_DELAY}"
echo "[start] prefixes: ${PREFIXES[*]}"

for prefix in "${PREFIXES[@]}"; do
  log_file="${OUT_DIR}/logs/fetch_${REPORT_YEAR}_${prefix}.log"
  python3 "${PY_SCRIPT}" \
    --report-year "${REPORT_YEAR}" \
    --start-date "${START_DATE}" \
    --end-date "${END_DATE}" \
    --out-dir "${OUT_DIR}" \
    --retry "${RETRY}" \
    --timeout "${TIMEOUT}" \
    --page-delay "${PAGE_DELAY}" \
    --sec-prefixes "${prefix}" \
    --manifest-suffix "_${prefix}" \
    >"${log_file}" 2>&1 &
  pid=$!
  pids+=("${pid}")
  prefixes+=("${prefix}")
  logs+=("${log_file}")
  echo "[spawn] prefix=${prefix} pid=${pid} log=${log_file}"
done

failed=0

for i in "${!pids[@]}"; do
  pid="${pids[$i]}"
  prefix="${prefixes[$i]}"
  log_file="${logs[$i]}"

  if wait "${pid}"; then
    rc=0
  else
    rc=$?
    failed=1
  fi

  echo "[done] prefix=${prefix} pid=${pid} exit_code=${rc} log=${log_file}"
done

if [[ "${failed}" -ne 0 ]]; then
  echo "[summary] at least one shard failed"
  exit 1
fi

echo "[summary] all shards completed successfully"
exit 0

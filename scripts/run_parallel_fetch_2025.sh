#!/usr/bin/env bash
#
# Usage:
#   bash scripts/run_parallel_fetch_2025.sh [START_DATE] [END_DATE] [OUT_DIR] [RETRY] [TIMEOUT]
# Example:
#   bash scripts/run_parallel_fetch_2025.sh 2025-01-01 2026-12-31 reports_raw 3 25
#

set -u

START_DATE="${1:-2025-01-01}"
END_DATE="${2:-2026-12-31}"
OUT_DIR="${3:-reports_raw}"
RETRY="${4:-3}"
TIMEOUT="${5:-25}"

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

echo "[start] START_DATE=${START_DATE} END_DATE=${END_DATE} OUT_DIR=${OUT_DIR} RETRY=${RETRY} TIMEOUT=${TIMEOUT}"
echo "[start] prefixes: ${PREFIXES[*]}"

for prefix in "${PREFIXES[@]}"; do
  log_file="${OUT_DIR}/logs/fetch_2025_${prefix}.log"
  python3 "${PY_SCRIPT}" \
    --start-date "${START_DATE}" \
    --end-date "${END_DATE}" \
    --out-dir "${OUT_DIR}" \
    --retry "${RETRY}" \
    --timeout "${TIMEOUT}" \
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

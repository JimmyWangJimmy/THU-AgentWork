# THU-AgentWork

This repository stores data and scripts for the first step of the project:
fetching **2025 annual report PDFs** for A-share listed companies (SSE, SZSE, BSE).

## What has been done

1. Created a crawler script:
   - `scripts/fetch_annual_reports_2025.py`
2. Implemented the workflow:
   - query CNINFO announcements API (`/new/hisAnnouncement/query`)
   - filter records containing `2025年年度报告` and excluding `摘要`
   - deduplicate by `secCode + report_year(2025)`, keep latest `announcementTime`
   - download PDFs concurrently with retry/backoff and resume support
3. Downloaded an initial verified sample run into:
   - `reports_raw/<stock_code>_<company_name>/2025/<announcement_id>.pdf`
4. Generated CSV outputs:
   - `reports_raw/download_manifest_2025.csv`
   - `reports_raw/download_failures_2025.csv`

## Directory layout

- `reports_raw/`: downloaded annual report PDFs and CSV logs
- `parsed_csv/`: parsed CSV outputs (next phase)
- `scripts/`: crawler and utility scripts

## Run the crawler

```bash
python3 scripts/fetch_annual_reports_2025.py \
  --start-date 2025-01-01 \
  --end-date 2026-12-31 \
  --out-dir reports_raw \
  --max-workers 4 \
  --retry 3
```

Optional test mode (small sample):

```bash
python3 scripts/fetch_annual_reports_2025.py --max-pages 2
```

## Notes

- Data source is CNINFO (official disclosure platform).
- This phase only handles downloading and traceable logging.
- PDF parsing to structured CSV fields will be implemented in the next phase.

## Progress log

- 2026-04-18 (full-run in progress):
  - continued full crawl and downloaded 624 report PDFs to `reports_raw/` (~1.9G).
  - switched to batch push strategy: push current snapshot first, then resume crawling.
  - after full crawl ends, rerun the crawler once to refresh:
    - `reports_raw/download_manifest_2025.csv`
    - `reports_raw/download_failures_2025.csv`
- 2026-04-18 (continued):
  - remote branch synced to commit `f2aa4f8` after resolving push timeout with smaller batches.
  - crawler networking improved to avoid TLS handshake stalls:
    - disabled system proxy auto-discovery in urllib opener
    - added periodic page-fetch progress logs
  - resumed segmented crawl and increased local PDF count to 669.
- 2026-04-19 (checkpoint):
  - full-window crawl progressed to download stage with stable pagination (`141` pages).
  - local PDF count reached `801` and was checkpointed for incremental push.
- 2026-04-19 (checkpoint-2):
  - resumed full-window crawl after push and reached local PDF count `894`.
  - continuing with small-batch commit/push strategy during full crawl.
- 2026-04-19 (checkpoint-3):
  - another full-window pass reached local PDF count `919`.
  - crawl/push loop remains stable with incremental batches.
- 2026-04-19 (parallel checkpoint):
  - enabled parallel crawling with multiple agent-assisted script upgrades.
  - switched to date-window shards; local PDF count reached `1466`.
- 2026-04-19 (refresh checkpoint):
  - completed a jan-apr refresh run with deduped `1494` records and `0` failures.
  - local PDF count reached `2083`.

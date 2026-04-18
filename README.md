# THU-AgentWork

[中文](#中文) | [English](#english)

---

## 中文

### 项目概览

这个仓库用于维护课程大作业第一阶段的数据资产与脚本，当前重点是抓取并整理 **2025 年 A 股上市公司年报 PDF**。

当前覆盖口径：
- 数据源：巨潮资讯（CNINFO）
- 市场范围：沪市、深市、北交所
- 报告类型：`2025年年度报告` 正文 PDF
- 去重规则：同一公司同一年仅保留最新披露版本作为 canonical 版本

### 仓库结构

```text
THU-AgentWork/
├── README.md                     # 中英双语项目说明
├── docs/                         # 项目文档
├── parsed_csv/                   # 后续解析结果目录
├── reports_raw/                  # 原始年报 PDF 与抓取清单
├── scripts/                      # 抓取与辅助脚本
└── tmp/                          # 本地临时目录（已忽略）
```

主要目录说明：
- `scripts/fetch_annual_reports_2025.py`：主抓取脚本
- `scripts/run_parallel_fetch_2025.sh`：并行抓取辅助脚本
- `scripts/push_untracked_pdf_batch.sh`：分批提交/推送原始 PDF 的辅助脚本
- `reports_raw/`：保存 PDF、manifest、failure CSV
- `parsed_csv/`：为下一阶段 PDF 解析结果预留
- `docs/`：保存设计文档、说明文档

如果后续对 `reports_raw/companies/` 做分桶整理，建议目录直接写成带说明的形式：

```text
companies/
├── 000_sz_main/    # 深市主板（常见 000 前缀）
├── 001_sz_main/    # 深市主板（001 前缀）
├── 002_sz_main/    # 深市原中小板代码段，现并入主板口径
├── 300_chinext/    # 创业板
├── 600_sh_main/    # 沪市主板
├── 601_sh_main/    # 沪市主板
├── 603_sh_main/    # 沪市主板
├── 688_star/       # 科创板
├── 900_sh_b/       # 沪市 B 股
└── 920_bse/        # 北交所
```

### 当前数据状态

截至最新一次完整性核查：
- 候选公告数：`4230`
- 过滤后年报正文数：`2122`
- 去重后 canonical 年报数：`1494`
- 抓取失败数：`0`
- `reports_raw/` 中现有 PDF 总数：`2083`
- 其中 canonical 最新版本：`1494`
- 其中历史/替代版本：`589`

权威核查文件：
- `reports_raw/download_manifest_2025_full_refresh.csv`
- `reports_raw/download_failures_2025_full_refresh.csv`

### 使用方法

全量抓取：

```bash
python3 scripts/fetch_annual_reports_2025.py \
  --start-date 2025-01-01 \
  --end-date 2026-12-31 \
  --out-dir reports_raw \
  --max-workers 4 \
  --retry 3
```

小样本测试：

```bash
python3 scripts/fetch_annual_reports_2025.py --max-pages 2
```

### 说明

- 当前阶段只负责“抓取到位、可复跑、可核查”。
- `reports_raw/` 中保留了部分历史版本 PDF，便于回溯，不等同于 canonical 口径。
- 运行日志、临时文件、虚拟环境不纳入仓库版本控制。

### 进度记录

- 2026-04-18：
  - 初步完成全量抓取链路搭建。
  - 下载并累计保存 `624` 份年报 PDF。
- 2026-04-18：
  - 解决推送超时问题，切换为小批次推送。
  - 优化网络请求，关闭系统代理自动发现，增加分页进度日志。
- 2026-04-19：
  - 多轮断点续跑与并行抓取后，本地 PDF 累计达到 `2083`。
  - 完成 jan-apr refresh，去重后 `1494` 条，失败 `0`。
  - 完成 full refresh verification：
    - 候选公告 `4230`
    - 去重后 `1494`
    - 缺失文件 `0`
    - 空文件 `0`

---

## English

### Overview

This repository stores scripts and data assets for the first phase of the course project. The current focus is fetching and organizing **2025 annual report PDFs for A-share listed companies**.

Current scope:
- Data source: CNINFO
- Exchanges: SSE, SZSE, BSE
- Report type: full `2025 Annual Report` PDF
- Deduplication rule: keep the latest disclosed version per company per year as the canonical version

### Repository Layout

```text
THU-AgentWork/
├── README.md                     # bilingual project guide
├── docs/                         # project documentation
├── parsed_csv/                   # parsed outputs for the next phase
├── reports_raw/                  # raw annual report PDFs and crawl manifests
├── scripts/                      # crawler and helper scripts
└── tmp/                          # local temporary directory (ignored)
```

Key paths:
- `scripts/fetch_annual_reports_2025.py`: main crawler
- `scripts/run_parallel_fetch_2025.sh`: helper for parallel crawl runs
- `scripts/push_untracked_pdf_batch.sh`: helper for batched PDF commits/pushes
- `reports_raw/`: PDFs, manifest CSVs, and failure CSVs
- `parsed_csv/`: reserved for the parsing stage
- `docs/`: design and project documents

If `reports_raw/companies/` is sharded later, the directory names should include both the code prefix and its meaning:

```text
companies/
├── 000_sz_main/    # SZSE main board (common 000 prefix)
├── 001_sz_main/    # SZSE main board (001 prefix)
├── 002_sz_main/    # historical SME-board code range, now under main-board scope
├── 300_chinext/    # ChiNext
├── 600_sh_main/    # SSE main board
├── 601_sh_main/    # SSE main board
├── 603_sh_main/    # SSE main board
├── 688_star/       # STAR Market
├── 900_sh_b/       # SSE B shares
└── 920_bse/        # Beijing Stock Exchange
```

### Current Data Status

As of the latest full verification run:
- Candidate announcements fetched: `4230`
- Filtered full annual reports: `2122`
- Deduplicated canonical reports: `1494`
- Download failures: `0`
- Total PDFs currently stored under `reports_raw/`: `2083`
- Canonical latest-version PDFs: `1494`
- Historical/replaced versions retained: `589`

Verification outputs:
- `reports_raw/download_manifest_2025_full_refresh.csv`
- `reports_raw/download_failures_2025_full_refresh.csv`

### Usage

Full crawl:

```bash
python3 scripts/fetch_annual_reports_2025.py \
  --start-date 2025-01-01 \
  --end-date 2026-12-31 \
  --out-dir reports_raw \
  --max-workers 4 \
  --retry 3
```

Small test run:

```bash
python3 scripts/fetch_annual_reports_2025.py --max-pages 2
```

### Notes

- This phase is limited to download, reproducibility, and traceable verification.
- `reports_raw/` intentionally keeps some historical PDF versions for auditability; that is different from the canonical deduplicated set.
- Runtime logs, temporary files, and local virtual environments are excluded from version control.

### Progress

- 2026-04-18:
  - Built the initial full-crawl workflow.
  - Downloaded and stored `624` report PDFs.
- 2026-04-18:
  - Switched to small-batch pushes after timeout issues.
  - Improved crawler networking by disabling proxy auto-discovery and adding pagination progress logs.
- 2026-04-19:
  - After multiple resumable and parallel runs, local PDF count reached `2083`.
  - Completed a jan-apr refresh with `1494` deduplicated records and `0` failures.
  - Completed a full refresh verification:
    - `4230` candidates fetched
    - `1494` canonical reports
    - `0` missing files
    - `0` empty files

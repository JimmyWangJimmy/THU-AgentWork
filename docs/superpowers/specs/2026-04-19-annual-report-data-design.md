# 2025 A-share Annual Report Data Design

## Context

This repository has completed the first project phase: crawling 2025 annual report PDFs for A-share listed companies from CNINFO into `reports_raw/`.

As of 2026-04-19, the local snapshot contains 2083 PDF files. The next phase is not additional bulk crawling, but converting the PDF corpus into a structured, research-grade data asset that supports:

- accounting and economics research
- cross-sectional and panel empirical analysis
- firm-level financial comparison and screening
- retrieval-augmented generation and question answering
- future parser iteration with traceable extraction evidence

The design goal is to preserve both raw evidence and normalized facts. The system should support Chinese annual reports with heterogeneous formatting, scanned pages, industry-specific accounts, and evolving disclosure requirements.

## Research Motivation

The field design should reflect what top accounting and economics papers actually use from annual reports, rather than only collecting generic financial statement rows.

### Textual disclosure variables

The literature repeatedly uses annual report text to measure:

- readability and complexity
- tone and negativity
- uncertainty and modal language
- forward-looking discussion
- length and boilerplate intensity
- year-over-year textual change

Representative references:

- Li (2008, Journal of Accounting and Economics): annual report readability, report length, earnings persistence
- Loughran and McDonald (2011): domain-specific financial sentiment and uncertainty dictionaries for annual report text
- Loughran and McDonald (2020): survey of textual analysis in accounting and finance

Implication: the dataset must retain full text, section text, and traceable sentence or paragraph evidence. A numeric-only extract is insufficient.

### Risk disclosure variables

The literature also uses annual report risk disclosures to study:

- risk topic exposure
- changes in risk factor disclosure
- investor response to new or removed risk language
- links between disclosure change and future firm outcomes

Representative references:

- Cohen, Malloy, and Nguyen: information in textual changes within mandated filings
- later accounting work on changes in risk factor disclosures and market response

Implication: risk disclosure should be stored at the item level, not only as one long chapter.

### Product market and industry structure variables

The annual report business description has been used to derive:

- product similarity
- endogenous industry classification
- competitor networks
- product lifecycle and market structure

Representative references:

- Hoberg and Phillips related work on text-based product market structure
- later Review of Financial Studies work using product text and annual report narratives

Implication: business overview and segment descriptions must be retained with clean text and section boundaries.

### Accounting and governance variables

Empirical accounting research also frequently uses:

- audit opinion
- internal control opinion
- goodwill and impairment
- related-party transactions
- customer and supplier concentration
- executive compensation and shareholding
- dividend policy
- litigation, guarantees, penalties, and major events

Implication: parsing should extend beyond the three statements and cover core governance and event disclosures.

## Disclosure Standard Constraints

The field design should align with both accounting statement structure and Chinese annual report disclosure rules.

- CSRC annual report content and format rules require sections covering company profile, major accounting data, management discussion and analysis, corporate governance, important matters, environmental and social responsibility, and financial report.
- PRC accounting standards and standard financial statement presentation imply preservation of the balance sheet, income statement, cash flow statement, statement of changes in equity, and key note disclosures.

Implication: storage should preserve both:

- standardized facts for comparison
- original labels and textual evidence for auditability

## Design Principles

### 1. Layered data asset, not a single wide table

The system should have four layers:

1. Evidence layer: original PDF, page images if needed, extracted raw text, raw table snippets, page numbers, source spans
2. Fact layer: normalized financial and disclosure facts with units and mappings
3. Feature layer: derived ratios, text metrics, risk topics, year-over-year deltas
4. Mart layer: task-specific tables for regression, screening, search, and LLM use

### 2. Long tables for heterogeneous facts

Financial statement data and many disclosure facts should be stored in long format so the system can handle:

- industry-specific line items
- changing report templates
- parent-only versus consolidated statements
- multiple versions of the same filing
- later schema expansion without destructive migration

### 3. Preserve source evidence for every extractable fact

Each extracted value should be traceable to:

- filing
- page number
- original row label or text span
- parser version
- confidence

This is required for quality control, human review, and later re-parsing.

### 4. Build for year-over-year comparison from day one

Many downstream research variables depend on changes relative to the prior annual report. The schema should therefore make it easy to compare same-firm filings across years even if the current corpus is centered on 2025 reports only.

## Recommended Data Scope

The recommended extraction scope is split into six blocks.

### A. Filing metadata

Required fields:

- `company_code`
- `company_name`
- `exchange`
- `board`
- `report_year`
- `filing_type`
- `announcement_id`
- `publish_date`
- `pdf_path`
- `pdf_sha256`
- `page_count`
- `language`
- `is_english_version`
- `currency`
- `unit_text`
- `auditor_name`
- `audit_opinion`
- `internal_control_audit_opinion`
- `signing_accountants`

### B. Section-level text

Required fields:

- standardized section name
- raw heading text
- section order
- page start and end
- full section text
- cleaned section text
- text hash

Core standardized sections:

- important notice
- company profile
- major accounting data
- management discussion and analysis
- risk factors
- principal business
- R&D
- corporate governance
- shareholders and actual controller
- directors, supervisors, executives
- dividend plan
- important matters
- financial statements
- notes to financial statements
- environmental and social responsibility

### C. Core financial statement facts

The system should extract both consolidated and parent-only values where disclosed.

#### Balance sheet

Minimum standardized items:

- cash and cash equivalents
- trading financial assets
- notes receivable
- accounts receivable
- receivables financing
- prepayments
- inventory
- contract assets
- other current assets
- long-term equity investments
- investment property
- fixed assets
- construction in progress
- right-of-use assets
- intangible assets
- development expenditure
- goodwill
- deferred tax assets
- short-term borrowings
- notes payable
- accounts payable
- contract liabilities
- employee compensation payable
- taxes payable
- other payables
- current portion of non-current liabilities
- long-term borrowings
- bonds payable
- lease liabilities
- deferred tax liabilities
- total assets
- total liabilities
- share capital
- capital reserve
- treasury shares
- other comprehensive income
- surplus reserve
- retained earnings
- minority interest
- total equity

#### Income statement

Minimum standardized items:

- revenue
- operating cost
- taxes and surcharges
- selling expense
- administrative expense
- R&D expense
- finance expense
- other income
- investment income
- fair value change income
- credit impairment loss
- asset impairment loss
- operating profit
- non-operating income
- non-operating expense
- total profit
- income tax expense
- net profit
- net profit attributable to parent
- minority profit
- other comprehensive income
- total comprehensive income
- basic EPS
- diluted EPS

#### Cash flow statement

Minimum standardized items:

- cash received from sale of goods and services
- tax refunds received
- other operating cash inflows
- cash paid for goods and services
- cash paid to and for employees
- taxes paid
- other operating cash outflows
- net cash flow from operating activities
- investment cash inflows
- capital expenditure paid
- acquisition cash paid
- other investment cash outflows
- net cash flow from investing activities
- financing cash inflows
- equity financing cash inflows
- debt repayment cash outflows
- dividends and interest paid
- lease payments
- net cash flow from financing activities
- foreign exchange effect
- net increase in cash
- beginning cash balance
- ending cash balance

#### Statement of changes in equity

At minimum, retain raw rows and a standardized map for:

- opening balance
- net profit
- other comprehensive income
- owner contributions
- profit appropriation
- dividends
- closing balance

### D. Key disclosure facts outside the statements

These fields are high-value for accounting, governance, and applied finance research.

Recommended fields:

- top five customer sales ratio
- top five supplier procurement ratio
- related-party transaction amount
- external guarantee amount
- major litigation flag and amount
- administrative penalty count and amount
- impairment event amount
- goodwill impairment amount
- dividend per share
- total cash dividend
- employee count
- R&D employee count
- overseas revenue
- segment revenue
- segment profit
- government subsidy amount
- major capital expenditure projects
- share pledge ratio
- actual controller change flag
- debt default or restructuring flag

### E. Risk item data

Each material risk item should be stored separately.

Required fields:

- risk heading
- risk text
- risk topic
- page start and end
- similarity to previous year
- new item flag
- removed item flag
- parser confidence

Suggested first-wave risk topics:

- macroeconomic risk
- policy and regulatory risk
- product demand risk
- competition and price war risk
- raw material cost risk
- foreign trade and tariff risk
- customer concentration risk
- supplier concentration risk
- technology and R&D risk
- environmental and safety risk
- litigation and compliance risk
- capital market and financing risk

### F. Text-derived features

Recommended features:

- total document length
- section length
- average sentence length
- readability or fog-like index
- negative word share
- positive word share
- uncertainty word share
- litigious word share
- strong modal word share
- weak modal word share
- forward-looking sentence share
- numeric density
- year-over-year document similarity
- section similarity
- risk item additions
- risk item deletions

## Recommended Schema

The schema should prioritize normalized core tables and keep marts downstream.

### 1. `companies`

Purpose:

- one row per listed company
- stable firm identity across filings

Core columns:

- `company_id`
- `company_code`
- `company_name`
- `exchange`
- `board`
- `industry_code`
- `industry_name`

### 2. `filings`

Purpose:

- one row per annual report filing instance

Core columns:

- `filing_id`
- `company_id`
- `report_year`
- `announcement_id`
- `publish_date`
- `filing_title`
- `filing_version`
- `pdf_path`
- `pdf_sha256`
- `page_count`
- `language`
- `currency`
- `unit_text`
- `auditor_name`
- `audit_opinion`
- `internal_control_audit_opinion`
- `extraction_status`

Uniqueness:

- unique on `announcement_id`
- optional business uniqueness on `(company_id, report_year, language, filing_version)`

### 3. `filing_sections`

Purpose:

- one row per section or subsection

Core columns:

- `section_id`
- `filing_id`
- `parent_section_id`
- `section_order`
- `section_level`
- `section_name_std`
- `section_name_raw`
- `page_start`
- `page_end`
- `text_raw`
- `text_clean`
- `text_hash`

### 4. `financial_facts`

Purpose:

- normalized long-form statement facts

Core columns:

- `fact_id`
- `filing_id`
- `statement_type`
- `scope_type`
- `period_type`
- `line_item_code`
- `line_item_label_std`
- `line_item_label_raw`
- `value`
- `unit_multiplier`
- `currency`
- `sign_normalized`
- `page_no`
- `note_ref`
- `confidence`

Recommended enumerations:

- `statement_type`: `balance_sheet`, `income_statement`, `cash_flow`, `changes_in_equity`
- `scope_type`: `consolidated`, `parent`
- `period_type`: `current_year`, `prior_year`, `opening_balance`, `closing_balance`

### 5. `financial_fact_mappings`

Purpose:

- preserves mapping from raw labels to standard line item codes

Core columns:

- `mapping_id`
- `raw_label`
- `line_item_code`
- `statement_type`
- `industry_scope`
- `mapping_rule_version`

### 6. `risk_items`

Purpose:

- one row per risk disclosure item

Core columns:

- `risk_item_id`
- `filing_id`
- `section_id`
- `risk_heading`
- `risk_text`
- `risk_topic`
- `page_start`
- `page_end`
- `similarity_prev_year`
- `is_new`
- `is_removed`
- `confidence`

### 7. `segment_facts`

Purpose:

- segment and geography disclosures

Core columns:

- `segment_fact_id`
- `filing_id`
- `segment_type`
- `segment_name`
- `metric_code`
- `metric_value`
- `page_no`
- `confidence`

### 8. `governance_facts`

Purpose:

- governance, ownership, executive, and internal control facts

Core columns:

- `governance_fact_id`
- `filing_id`
- `fact_type`
- `fact_name`
- `fact_value_text`
- `fact_value_numeric`
- `unit_text`
- `page_no`
- `confidence`

### 9. `major_events`

Purpose:

- one row per major event disclosure

Core columns:

- `event_id`
- `filing_id`
- `event_type`
- `event_title`
- `event_text`
- `event_amount`
- `page_start`
- `page_end`
- `confidence`

### 10. `text_features`

Purpose:

- precomputed document and section features for research and modeling

Core columns:

- `feature_id`
- `filing_id`
- `section_id`
- `feature_name`
- `feature_value`
- `feature_version`

### 11. `extraction_evidence`

Purpose:

- stores provenance for facts and text items

Core columns:

- `evidence_id`
- `entity_type`
- `entity_id`
- `filing_id`
- `page_no`
- `source_snippet`
- `source_bbox`
- `parser_name`
- `parser_version`
- `confidence`

## Storage Strategy

### Primary storage

Recommended primary storage:

- relational tables for normalized facts and metadata
- parquet snapshots for large analytical extracts

For this repository stage, it is acceptable to begin with:

- CSV or parquet outputs under `parsed_csv/`
- a schema file that can later map to SQLite, DuckDB, or Postgres

### Content retention rules

Retain:

- original PDF path
- raw section text
- raw row labels for statements
- page-level evidence

Do not rely only on:

- final normalized line item codes
- final feature tables

The raw-to-standard mapping is part of the data asset and should not be discarded.

## Extraction Phasing

### Phase 1: foundation extraction

Deliverables:

- filing metadata
- section segmentation
- full text extraction
- core financial statements in long format
- evidence table

Why first:

- this creates immediate research value
- this supports later refinement without schema redesign

### Phase 2: high-value disclosures

Deliverables:

- risk items
- segment facts
- audit and internal control fields
- top customer and supplier concentration
- R&D and employee disclosures
- dividend plan

### Phase 3: derived features

Deliverables:

- ratios
- text metrics
- year-over-year changes
- risk topic taxonomy
- similarity and boilerplate measures

### Phase 4: downstream marts

Deliverables:

- regression-ready firm-year panel
- search and RAG index
- investment screening table
- peer-comparison datasets

## Downstream Use Cases

### Academic empirical research

The design should support regressions such as:

- earnings persistence on readability
- investment or financing behavior on policy-risk exposure
- market reaction on risk disclosure change
- impairment, audit opinion, or internal control issues on textual uncertainty and governance variables

### Investment and strategy analysis

The design should support screens such as:

- firms with rising revenue but weakening operating cash flow
- firms adding competition or price-war risk language
- firms with high customer concentration and falling margins
- firms with rising R&D intensity but weak commercialization outcomes

### Retrieval and LLM workflows

The design should support queries such as:

- find all firms that newly disclosed tariff risk in 2025
- find all annual reports with qualified audit opinions
- show companies with negative operating cash flow but positive reported profit
- retrieve the exact page and paragraph discussing customer concentration

### Future parser iteration

Because extraction quality will improve over time, the design must support:

- parser versioning
- confidence thresholds
- reprocessing of only selected tables
- reconciliation across parser versions

## Recommended Immediate Deliverables

The next design artifacts should be:

1. `field_dictionary.md`
2. `schema.sql` or `schema.md`
3. parser output contracts for `filings`, `filing_sections`, `financial_facts`, and `extraction_evidence`

These should be finalized before large-scale PDF parsing begins.

## Recommendation

The recommended target architecture is:

- preserve raw evidence
- normalize facts in long tables
- compute derived features separately
- publish narrow marts for downstream tasks

This is preferable to a single firm-year wide table because a wide table will be fragile under:

- industry-specific accounting line items
- parent versus consolidated statements
- disclosure heterogeneity
- future expansion into governance, ESG, and textual research variables

## Sources

- Li, F. 2008. Annual report readability, current earnings, and earnings persistence. Journal of Accounting and Economics.
- Loughran, T., and McDonald, B. 2011. When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks.
- Loughran, T., and McDonald, B. 2020. Textual analysis in accounting and finance: A survey.
- Cohen, L., Malloy, C., and Nguyen, Q. related work on textual changes in SEC filings.
- Hoberg, G., and Phillips, G. related work on text-based product market structure.
- CSRC annual report disclosure rules.
- PRC accounting statement presentation requirements.

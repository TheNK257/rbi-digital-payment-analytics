# RBI Bank-Wise Digital Payment Performance Analytics (2020 – 2024)
### Business Intelligence (23UDSPEL4704A) — Technical Assessment Exercise 2 (TAE 2)
**B.Tech CSE (Data Science) | Winter 2026**  
**G H Raisoni College of Engineering and Management, Pune**

---

## Executive Summary
This project implements an end-to-end Business Intelligence (BI) and Data Warehousing solution analyzing bank-wise digital payment performance across India over a **60-month historical timeframe (January 2020 – December 2024)**. 

The raw dataset is extracted directly from the official **Reserve Bank of India (RBI)** portal (`https://www.rbi.org.in`), capturing payment infrastructure (ATMs, PoS, Micro ATMs, QR Codes) and transactional volumes/values across **Credit Cards** and **Debit Cards** for over **180 Scheduled Commercial, Public, Private, Foreign, Small Finance, and Payments Banks**.

The project delivers:
1. **Automated Web Scraper** (`scraper/scrape_rbi.py`) acquiring 60 months of heterogeneous HTML data.
2. **Robust ETL Pipeline** (`etl/etl.py`) handling multi-regime schema evolution, unit unification (Actuals vs Lakhs vs Thousands), bank name reconciliation, and post-2020 mega-mergers.
3. **Dimensional Data Warehouse** (`database/schema.sql` & `database/load.py`) modeled as an optimized **Star Schema** in MySQL & SQLite with surrogate keys and analytical views.
4. **Interactive Power BI Dashboard** connected to the dimensional model showcasing 6 core business KPIs, drill-downs, and trend analytics.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA ACQUISITION                               │
│  Reserve Bank of India (RBI) Bank-wise ATM/POS/Card Statistics (HTML)   │
│  60 Monthly Releases (Jan 2020 – Dec 2024) [atmid: 107 → 166]           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      RAW DATA STAGING LAYER                             │
│  60 Uncleaned CSV Files (raw_data/atm_YYYY_MM.csv)                      │
│  Proof of Messy Data: Inconsistent Colspans, Evolving Schemas, Mixed Units│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PYTHON ETL & TRANSFORMATION                        │
│  • Format Alignment across 3 Historical RBI Regimes (14, 17, 28 cols)   │
│  • Bank Name Normalization (180+ variations mapped to standard names)   │
│  • Public Sector Bank Mega-Merger Harmonization (Anchor Bank Tracking)  │
│  • Currency Unit Standardization (Normalized into INR Lakhs)            │
│  • Data Quality & Reporting Audit (is_reported boolean flag)            │
│  Output: cleaned_data/cleaned_transactions.csv (3,781 clean records)    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIMENSIONAL DATA WAREHOUSE                           │
│  Database: rbi_banking_bi (MySQL 8.0+ / SQLite Local Mirror)            │
│  Star Schema: 1 Central Fact Table + 4 Dimension Tables                 │
│  • Fact_Transaction  (Metrics, Volumes, Values, Card Bases)             │
│  • Dim_Date          (Temporal Hierarchy: Year, Quarter, Month, FY)     │
│  • Dim_Bank          (Bank Profiles, Anchor Entity, Merger Details)     │
│  • Dim_BankCategory  (Sectors: Public, Private, Foreign, SFB, Payments) │
│  • Dim_Channel       (Delivery Channels: ATM, POS, E-Commerce, QR)      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   INTERACTIVE POWER BI DASHBOARD                        │
│  • 6 Core KPIs & Drill-Downs (ATM Trends, POS Terminal Dominance,       │
│    Credit Card Issuance, Debit Card Digital vs ATM Shift, Heatmaps)     │
│  • Dynamic Slicers: Year, Sector, Anchor Bank, Category                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Project Repository Structure

```
BI/
├── .gitignore                      # Git exclusion rules
├── README.md                       # Comprehensive Technical Documentation
├── scraper/
│   └── scrape_rbi.py               # Scrapes 60 months of RBI HTML tables (atmid 107-166)
├── etl/
│   └── etl.py                      # Multi-format harmonization & cleaning pipeline
├── database/
│   ├── schema.sql                  # MySQL Star Schema DDL, Foreign Keys & Analytical Views
│   ├── load.py                     # Data loader script (MySQL + SQLite + CSV exports)
│   ├── rbi_banking_bi.db           # SQLite warehouse database mirror
│   └── star_schema_tables/         # Individual dimension & fact CSVs for instant BI import
│       ├── Dim_Date.csv
│       ├── Dim_Bank.csv
│       ├── Dim_BankCategory.csv
│       ├── Dim_Channel.csv
│       └── Fact_Transaction.csv
├── raw_data/                       # 60 Scraped Raw Monthly CSVs (Proof of raw sourcing)
│   ├── atm_2020_01.csv
│   ├── atm_2020_02.csv
│   └── ... (60 files)
├── cleaned_data/
│   └── cleaned_transactions.csv    # 3,781 Clean, normalized master transaction records
└── dashboard/
    ├── RBI_Banking_BI.pbix         # Interactive Power BI Dashboard
    ├── generate_visual_mockups.py  # Visual preview generation script
    └── visual_previews/            # 6 PNG reference KPI charts
```

---

## ETL Transformation Details & Data Quality Fixes

During the 2020–2024 period, RBI reporting underwent substantial real-world changes. The ETL pipeline programmatically handles:

| Data Challenge | Raw RBI Issue | ETL Transformation Solution |
|---|---|---|
| **Evolving Column Schemas** | **Regime 1 (2020):** 14 columns.<br>**Regime 2 (2020–2022):** 17 columns (added Micro ATMs).<br>**Regime 3 (2022–2024):** 28 columns (split into PoS, E-com, QR). | Unified canonical schema mapping ATM, POS, E-Commerce, Card counts, and monetary amounts into consistent metrics. |
| **Mixed Unit Conventions** | 2020–2021 reported values in **Lakhs** (₹ 100,000).<br>2022–2024 reported in **Thousands** (₹ '000). | Values in ₹ '000 are divided by `100.0` to standardize all financial metrics strictly into **INR Lakhs**. |
| **Inconsistent Bank Naming** | Raw text variations: `"HDFC BANK LTD"`, `"HDFC"`, `"HONGKONG AND SHANGHAI BKG CORPN"` vs `"HSBC LTD"`. | Standardized dictionary mapping 180+ bank name variations into official entity names. |
| **Bank Mega-Mergers** | April 2020 public sector mergers (e.g., Allahabad Bank into Indian Bank; Corporation Bank & Andhra Bank into Union Bank). | Preserved historical reporting while tagging each bank with its `anchor_bank`, `is_merged` flag, and `merge_year`. |
| **Ambiguous Zeros / Missing Data** | Inactive or non-reporting banks (e.g. newly licensed Payments/Small Finance Banks) listed with zeros or missing rows. | Engineered `is_reported` boolean flag to distinguish between non-reporting periods and active zero balances. |

---

## Dimensional Model (Star Schema)

The database `rbi_banking_bi` is organized into an enterprise **Star Schema** comprising **1 central Fact table** and **4 Dimension tables** connected via 1-to-Many (`1:N`) referential integrity constraints.

### Star Schema Architecture Diagram

```
                             ┌──────────────────────────────────────┐
                             │               Dim_Date               │
                             ├──────────────────────────────────────┤
                             │ PK  date_key (INT, YYYYMM)           │
                             │     year (INT)                       │
                             │     month (INT, 1-12)                │
                             │     month_name (VARCHAR, Jan-Dec)    │
                             │     quarter (VARCHAR, Q1-Q4)         │
                             │     fiscal_year (VARCHAR, FY20-21...)│
                             │  *  Year (Categorical) (Calculated)  │
                             └──────────────────┬───────────────────┘
                                                │
                                                │ 1
                                                │
                                                │ N
┌───────────────────────────────┐               ▼               ┌───────────────────────────────┐
│           Dim_Bank            │    ┌─────────────────────┐    │       Dim_BankCategory        │
├───────────────────────────────┤    │  Fact_Transaction   │    ├───────────────────────────────┤
│ PK  bank_key (INT)            │◄───┤ PK  txn_id (BIGINT) ├───►│ PK  category_key (INT)        │
│     bank_name (VARCHAR)       │ 1:N│ FK  date_key (INT)  │N:1 │     category_name (VARCHAR)   │
│     anchor_bank (VARCHAR)     │    │ FK  bank_key (INT)  │    │     sector (VARCHAR)          │
│     is_merged (BOOLEAN)       │    │ FK  category_key    │    └───────────────────────────────┘
│     merge_year (INT)          │    │ FK  channel_key     │
└───────────────────────────────┘    │                     │
                                     │  Infrastructure:    │
                                     │  • atm_onsite_count │
                                     │  • atm_offsite_count│
                                     │  • atm_total_count  │
┌───────────────────────────────┐    │  • pos_online_count │
│          Dim_Channel          │    │  • micro_atm_count  │
├───────────────────────────────┤    │                     │
│ PK  channel_key (INT)         │    │  Card Base:         │
│     channel_name (VARCHAR)    │    │  • credit_cards_out │
│     channel_type (VARCHAR)    │    │  • debit_cards_out  │
│     is_digital (BOOLEAN)      │    │                     │
└───────────────┬───────────────┘    │  Volumes:           │
                │                    │  • credit_txn_atm_vol
                │ 1                  │  • credit_txn_pos_vol
                │                    │  • debit_txn_atm_vol│
                │ N                  │  • debit_txn_pos_vol│
                └───────────────────►│                     │
                                     │  Values (₹ Lakhs):  │
                                     │  • credit_atm_val   │
                                     │  • credit_pos_val   │
                                     │  • credit_total_val │
                                     │  • debit_atm_val    │
                                     │  • debit_pos_val    │
                                     │  • debit_total_val  │
                                     │                     │
                                     │  Audit:             │
                                     │  • is_reported      │
                                     └─────────────────────┘
```

### Power BI Semantic Model Enhancements (Tabular Layer)

To optimize interactive dashboard responsiveness and reporting accuracy, the following enhancements were engineered directly into the Power BI tabular model:

1. **Chronological Calendar Sorting:**
   - `Dim_Date[month_name]` is mapped with `Sort By Column = month` to ensure chronological reporting (`January` ➔ `December`) across all matrices and charts.

2. **Categorical Timeline Support:**
   - Calculated column `Dim_Date[Year (Categorical)]` converts numeric years into formatted strings (`"2020"` to `"2024"`), preventing continuous hairline rendering and ensuring full-width column bars.

3. **Drill-Down Hierarchies:**
   - **`Calendar Hierarchy`:** `Year` ➔ `Quarter` ➔ `Month`
   - **`Fiscal Hierarchy`:** `Fiscal Year` ➔ `Quarter` ➔ `Month`
   - **`Sector Hierarchy`:** `Sector` ➔ `Bank Category`
   - **`Bank Entity Hierarchy`:** `Anchor Bank` ➔ `Bank Name` (drill down from merged anchor to constituent entities)

4. **35 Curated DAX Measures (Organized into 6 Display Folders):**
   - **`1. Infrastructure Metrics`:** `[Total ATMs]`, `[On-Site ATMs]`, `[Off-Site ATMs]`, `[Off-Site ATM Share %]`, `[Total POS Terminals]`, `[Total Micro ATMs]`, `[Total Acceptance Touchpoints]`
   - **`2. Card Issuance`:** `[Total Credit Cards]`, `[Total Debit Cards]`, `[Total Cards in Force]`, `[Credit Card Share %]`, `[Debit Card Share %]`
   - **`3. Transaction Volumes`:** `[Debit ATM Txn Volume]`, `[Debit POS Txn Volume]`, `[Total Debit Txn Volume]`, `[Credit POS Txn Volume]`, `[Total Digital Txn Volume]`, `[Debit Digital Volume %]`, `[Debit Cash Volume %]`
   - **`4. Transaction Values (Lakh / Cr)`:** `[Credit POS Txn Value (Lakh)]`, `[Total Credit Txn Value (Lakh)]`, `[Debit POS Txn Value (Lakh)]`, `[Total Digital Spend (Lakh)]`, `[Total Digital Spend (Cr)]`, `[Total Card Spend (Cr)]`
   - **`5. Ticket Sizes & Ratios`:** `[Avg Credit POS Ticket Size (Rs)]`, `[Avg Debit POS Ticket Size (Rs)]`, `[Avg Debit ATM Withdrawal (Rs)]`
   - **`6. Model Metadata`:** `[Reporting Banks Count]`, `[Reporting Periods Count]`

---

## 6 Power BI KPI Visuals

| # | Visual Title | Chart Type | Fields & Dimensions | Core Business Insight |
|---|---|---|---|---|
| **1** | **ATM Deployment Trend: Public vs. Private** | Line Chart | **X-Axis:** Date (`year-month`)<br>**Y-Axis:** Total ATMs (`atm_total_count`)<br>**Legend:** Bank Category | Public sector banks maintain over 65% of physical ATMs, while private banks prioritize off-site digital kiosks. |
| **2** | **Top 10 Banks by Credit Card Base (2024)** | Horizontal Bar | **Y-Axis:** Bank Name<br>**X-Axis:** Credit Cards Outstanding | HDFC Bank, SBI, ICICI Bank, and Axis Bank capture over 72% of India's total credit card circulation. |
| **3** | **POS Terminal Growth by Sector** | Clustered Column | **X-Axis:** Year (2020–2024)<br>**Y-Axis:** POS Count (`pos_online_count`)<br>**Legend:** Sector | Private banks drove an exponential 4x expansion in merchant POS & QR acceptance post-2021. |
| **4** | **Debit Card Usage Shift: ATM vs. POS/E-Com** | 100% Stacked Bar | **X-Axis:** Year<br>**Y-Axis:** Volume %<br>**Legend:** ATM Withdrawal Vol vs POS Vol | Dramatic shift from cash withdrawals towards POS & online merchant spend (digital volume share grew from 38% to 64%). |
| **5** | **Monthly Transaction Value Heatmap** | Matrix Heatmap | **Rows:** Bank Category<br>**Columns:** Month Name<br>**Values:** Credit POS Value (Lakh) | Highlights intense Q3–Q4 festive spending surges (October–December) across private cardholders. |
| **6** | **Pre/Post Merger Bank Volume Continuity** | Multi-Line Chart | **X-Axis:** Year (2019–2022)<br>**Y-Axis:** Debit/Credit Volume<br>**Filter:** Merged Entities | Demonstrates smooth absorption of transaction volume from merged entities into anchor banks. |

---

## Execution & Setup Guide

### 1. Prerequisites
- Python 3.10+
- MySQL Server 8.0+ (or use the built-in SQLite mirror `database/rbi_banking_bi.db`)
- Power BI Desktop (Windows)

### 2. Install Dependencies
```bash
pip install requests beautifulsoup4 pandas sqlalchemy pymysql mysql-connector-python python-pptx
```

### 3. Run the Scraper (Downloads 60 raw CSVs from RBI)
```bash
python scraper/scrape_rbi.py
```

### 4. Run the ETL Pipeline (Harmonizes and Cleans Data)
```bash
python etl/etl.py
```
*Output: `cleaned_data/cleaned_transactions.csv` (3,781 clean records).*

### 5. Load into Data Warehouse
```bash
# To populate SQLite and export individual Star Schema CSV tables:
python database/load.py

# To populate MySQL directly:
python database/load.py <your_mysql_root_password>
```

### 6. Connect in Power BI Desktop
1. Open **Power BI Desktop**.
2. **Option A (Direct MySQL):**
   - Click **Get Data** → **MySQL Database**.
   - Server: `localhost`, Database: `rbi_banking_bi`.
   - Select `Fact_Transaction`, `Dim_Date`, `Dim_Bank`, `Dim_BankCategory`, `Dim_Channel`.
3. **Option B (Direct CSV Import):**
   - Click **Get Data** → **Folder** or **Text/CSV**.
   - Browse to `database/star_schema_tables/` and load the 5 pre-built dimensional tables.
4. Verify relationships in **Model View** (1-to-many from Dimensions to Fact).

---

## Authors & Academic Credentials
- **Student 1:** Naman Kadam | Final Year B.Tech CSE (Data Science)
- **Course:** Business Intelligence (23UDSPEL4704A)
- **Institution:** G H Raisoni College of Engineering and Management, Pune
- **Teacher:** Mr. Chinmay Mukim
- **Head of Department:** Dr. Deepika Ajalkar

-- ==============================================================================
-- TAE 2: Reserve Bank of India (RBI) Digital Payment Analytics Data Warehouse
-- Star Schema Dimensional Model DDL
-- Database: rbi_banking_bi
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS rbi_banking_bi
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE rbi_banking_bi;

-- Drop existing tables to allow clean recreation
DROP TABLE IF EXISTS Fact_Transaction;
DROP TABLE IF EXISTS Dim_Channel;
DROP TABLE IF EXISTS Dim_BankCategory;
DROP TABLE IF EXISTS Dim_Bank;
DROP TABLE IF EXISTS Dim_Date;

-- ------------------------------------------------------------------------------
-- 1. Dim_Date: Temporal Dimension covering monthly periods (2020 - 2024)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Date (
    date_key INT PRIMARY KEY,                 -- YYYYMM format (e.g., 202001)
    year INT NOT NULL,                        -- 2020 - 2024
    month INT NOT NULL,                       -- 1 - 12
    month_name VARCHAR(15) NOT NULL,          -- January, February, etc.
    quarter VARCHAR(5) NOT NULL,              -- Q1, Q2, Q3, Q4
    fiscal_year VARCHAR(10) NOT NULL,         -- FY2019-20, FY2020-21, etc.
    INDEX idx_dim_date_year (year),
    INDEX idx_dim_date_fy (fiscal_year)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 2. Dim_Bank: Bank entity dimension including merger mappings
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Bank (
    bank_key INT AUTO_INCREMENT PRIMARY KEY,
    bank_name VARCHAR(150) NOT NULL UNIQUE,
    anchor_bank VARCHAR(150) NOT NULL,
    is_merged BOOLEAN NOT NULL DEFAULT FALSE,
    merge_year INT DEFAULT NULL,
    INDEX idx_dim_bank_anchor (anchor_bank),
    INDEX idx_dim_bank_merged (is_merged)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 3. Dim_BankCategory: Classification Dimension (Public, Private, Foreign, etc.)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_BankCategory (
    category_key INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(80) NOT NULL UNIQUE,
    sector VARCHAR(50) NOT NULL,
    INDEX idx_dim_category_sector (sector)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 4. Dim_Channel: Delivery Channel Dimension (ATM, POS, Online, Digital)
-- ------------------------------------------------------------------------------
CREATE TABLE Dim_Channel (
    channel_key INT AUTO_INCREMENT PRIMARY KEY,
    channel_name VARCHAR(50) NOT NULL UNIQUE,
    channel_type VARCHAR(50) NOT NULL,
    is_digital BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 5. Fact_Transaction: Central Fact Table for Bank Performance Metrics
-- ------------------------------------------------------------------------------
CREATE TABLE Fact_Transaction (
    txn_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    date_key INT NOT NULL,
    bank_key INT NOT NULL,
    category_key INT NOT NULL,
    channel_key INT NOT NULL DEFAULT 1,

    -- Infrastructure Counts
    atm_onsite_count INT NOT NULL DEFAULT 0,
    atm_offsite_count INT NOT NULL DEFAULT 0,
    atm_total_count INT NOT NULL DEFAULT 0,
    pos_online_count INT NOT NULL DEFAULT 0,
    micro_atm_count INT NOT NULL DEFAULT 0,

    -- Card Base Counts
    credit_cards_outstanding BIGINT NOT NULL DEFAULT 0,
    debit_cards_outstanding BIGINT NOT NULL DEFAULT 0,

    -- Transaction Volumes (Number of Transactions)
    credit_txn_atm_vol BIGINT NOT NULL DEFAULT 0,
    credit_txn_pos_vol BIGINT NOT NULL DEFAULT 0,
    debit_txn_atm_vol BIGINT NOT NULL DEFAULT 0,
    debit_txn_pos_vol BIGINT NOT NULL DEFAULT 0,

    -- Transaction Values (Standardized in INR Lakhs)
    credit_txn_atm_value_lakh DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    credit_txn_pos_value_lakh DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    credit_txn_total_value_lakh DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    debit_txn_atm_value_lakh DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    debit_txn_pos_value_lakh DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    debit_txn_total_value_lakh DECIMAL(18, 2) NOT NULL DEFAULT 0.00,

    -- Data Quality / Reporting Flag
    is_reported BOOLEAN NOT NULL DEFAULT TRUE,

    -- Foreign Key Constraints
    CONSTRAINT fk_fact_date FOREIGN KEY (date_key) 
        REFERENCES Dim_Date(date_key) ON DELETE RESTRICT,
    CONSTRAINT fk_fact_bank FOREIGN KEY (bank_key) 
        REFERENCES Dim_Bank(bank_key) ON DELETE RESTRICT,
    CONSTRAINT fk_fact_category FOREIGN KEY (category_key) 
        REFERENCES Dim_BankCategory(category_key) ON DELETE RESTRICT,
    CONSTRAINT fk_fact_channel FOREIGN KEY (channel_key) 
        REFERENCES Dim_Channel(channel_key) ON DELETE RESTRICT,

    -- Performance Indexes
    INDEX idx_fact_date_bank (date_key, bank_key),
    INDEX idx_fact_category (category_key),
    INDEX idx_fact_reported (is_reported)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 6. Analytical Views for Business Intelligence & Power BI
-- ------------------------------------------------------------------------------

-- View 1: Top 10 Banks by Credit Card Base in 2024
CREATE OR REPLACE VIEW vw_top10_credit_cards_2024 AS
SELECT 
    b.bank_name,
    c.category_name,
    MAX(f.credit_cards_outstanding) AS peak_credit_cards_2024,
    ROUND(SUM(f.credit_txn_total_value_lakh), 2) AS total_annual_cc_value_lakh
FROM Fact_Transaction f
JOIN Dim_Bank b ON f.bank_key = b.bank_key
JOIN Dim_BankCategory c ON f.category_key = c.category_key
JOIN Dim_Date d ON f.date_key = d.date_key
WHERE d.year = 2024 AND f.is_reported = TRUE
GROUP BY b.bank_name, c.category_name
ORDER BY peak_credit_cards_2024 DESC
LIMIT 10;

-- View 2: Public vs Private Sector Infrastructure Growth Trend
CREATE OR REPLACE VIEW vw_public_vs_private_growth AS
SELECT 
    d.year,
    c.category_name,
    SUM(f.atm_total_count) AS total_atms,
    SUM(f.pos_online_count) AS total_pos_terminals,
    SUM(f.credit_cards_outstanding) AS total_credit_cards,
    SUM(f.debit_cards_outstanding) AS total_debit_cards,
    ROUND(SUM(f.credit_txn_total_value_lakh), 2) AS total_cc_spend_lakh,
    ROUND(SUM(f.debit_txn_total_value_lakh), 2) AS total_dc_spend_lakh
FROM Fact_Transaction f
JOIN Dim_BankCategory c ON f.category_key = c.category_key
JOIN Dim_Date d ON f.date_key = d.date_key
WHERE c.category_name IN ('Public Sector', 'Private Sector') AND f.is_reported = TRUE
GROUP BY d.year, c.category_name
ORDER BY d.year, c.category_name;

-- View 3: Debit Card ATM vs POS Transition (Digital Shift)
CREATE OR REPLACE VIEW vw_digital_shift_debit_cards AS
SELECT 
    d.year,
    SUM(f.debit_txn_atm_vol) AS atm_withdrawal_volume,
    SUM(f.debit_txn_pos_vol) AS pos_ecom_purchase_volume,
    ROUND(SUM(f.debit_txn_atm_value_lakh), 2) AS atm_withdrawal_value_lakh,
    ROUND(SUM(f.debit_txn_pos_value_lakh), 2) AS pos_purchase_value_lakh,
    ROUND(SUM(f.debit_txn_pos_vol) * 100.0 / NULLIF(SUM(f.debit_txn_atm_vol + f.debit_txn_pos_vol), 0), 2) AS digital_volume_share_pct
FROM Fact_Transaction f
JOIN Dim_Date d ON f.date_key = d.date_key
WHERE f.is_reported = TRUE
GROUP BY d.year
ORDER BY d.year;

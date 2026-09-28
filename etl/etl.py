"""
ETL Pipeline for RBI Bankwise ATM/POS/Card Statistics (2020 - 2024)
Cleans 60 monthly raw CSV files and creates cleaned_data/cleaned_transactions.csv.
Applies:
- Header alignment across 3 RBI reporting formats
- Bank name normalization
- Bank merger mapping to anchor banks
- Standardized currency units (all values in INR Lakhs)
- Sector and Bank Category classification
- Reporting status flag (is_reported)
"""

import os
import glob
import re
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
CLEANED_DIR = os.path.join(BASE_DIR, "cleaned_data")
OUTPUT_CSV = os.path.join(CLEANED_DIR, "cleaned_transactions.csv")

# Bank Name Normalization Mapping
BANK_NORMALIZE = {
    "STATE BANK OF INDIA": "State Bank of India",
    "SBI": "State Bank of India",
    "PUNJAB NATIONAL BANK": "Punjab National Bank",
    "PNB": "Punjab National Bank",
    "BANK OF BARODA": "Bank of Baroda",
    "BOB": "Bank of Baroda",
    "CANARA BANK": "Canara Bank",
    "UNION BANK OF INDIA": "Union Bank of India",
    "BANK OF INDIA": "Bank of India",
    "INDIAN BANK": "Indian Bank",
    "CENTRAL BANK OF INDIA": "Central Bank of India",
    "INDIAN OVERSEAS BANK": "Indian Overseas Bank",
    "UCO BANK": "UCO Bank",
    "BANK OF MAHARASHTRA": "Bank of Maharashtra",
    "PUNJAB AND SIND BANK": "Punjab & Sind Bank",
    "PUNJAB & SIND BANK": "Punjab & Sind Bank",
    "IDBI LTD": "IDBI Bank",
    "IDBI BANK LIMITED": "IDBI Bank",
    "IDBI BANK LTD": "IDBI Bank",

    # Merged Banks
    "ALLAHABAD BANK": "Allahabad Bank",
    "ANDHRA BANK": "Andhra Bank",
    "CORPORATION BANK": "Corporation Bank",
    "ORIENTAL BANK OF COMMERCE": "Oriental Bank of Commerce",
    "UNITED BANK OF INDIA": "United Bank of India",
    "SYNDICATE BANK": "Syndicate Bank",
    "THE LAXMI VILAS BANK LTD": "Laxmi Vilas Bank",
    "LAXMI VILAS BANK": "Laxmi Vilas Bank",

    # Private Banks
    "HDFC BANK LTD": "HDFC Bank",
    "ICICI BANK LTD": "ICICI Bank",
    "AXIS BANK LTD": "Axis Bank",
    "KOTAK MAHINDRA BANK LTD": "Kotak Mahindra Bank",
    "INDUSIND BANK LTD": "IndusInd Bank",
    "YES BANK LTD": "Yes Bank",
    "FEDERAL BANK LTD": "Federal Bank",
    "IDFC FIRST BANK LTD": "IDFC First Bank",
    "IDFC BANK LIMITED": "IDFC First Bank",
    "BANDHAN BANK LTD": "Bandhan Bank",
    "RBL BANK LTD": "RBL Bank",
    "RATNAKAR BANK LIMITED": "RBL Bank",
    "SOUTH INDIAN BANK": "South Indian Bank",
    "CITY UNION BANK": "City Union Bank",
    "KARUR VYSYA BANK LTD": "Karur Vysya Bank",
    "KARNATAKA BANK LTD": "Karnataka Bank",
    "TAMILNAD MERCANTILE BANK LTD": "Tamilnad Mercantile Bank",
    "DCB BANK LTD": "DCB Bank",
    "DHANALAKSHMI BANK LTD": "Dhanlaxmi Bank",
    "CATHOLIC SYRIAN BANK LTD": "CSB Bank",
    "CSB BANK LIMITED": "CSB Bank",
    "JAMMU AND KASHMIR BANK": "J&K Bank",
    "JAMMU AND KASHMIR BANK LTD": "J&K Bank",
    "NAINITAL BANK LTD": "Nainital Bank",

    # Foreign Banks
    "CITI BANK": "Citi Bank",
    "STANDARD CHARTERED BANK LTD": "Standard Chartered Bank",
    "HONGKONG AND SHANGHAI BKG CORPN": "HSBC",
    "HSBC LTD": "HSBC",
    "AMERICAN EXPRESS": "American Express",
    "AMERICAN EXPRESS BANKING CORPORATION": "American Express",
    "DBS BANK": "DBS Bank",
    "DBS INDIA BANK LTD": "DBS Bank",
    "DEUTSCHE BANK LTD": "Deutsche Bank",
    "BARCLAYS BANK PLC": "Barclays Bank",
    "BANK OF AMERICA": "Bank of America",
    "DOHA BANK Q.P.S.C.": "Doha Bank",
    "SBM BANK INDIA LTD": "SBM Bank",
    "WOORI BANK": "Woori Bank",
    "KEB HANA BANK": "KEB Hana Bank",
    "KOOKMIN BANK": "Kookmin Bank",
    "BANK OF BAHRAIN & KUWAIT B.S.C.": "Bank of Bahrain & Kuwait",

    # Payments Banks
    "PAYTM PAYMENTS BANK": "Paytm Payments Bank",
    "AIRTEL PAYMENTS BANK": "Airtel Payments Bank",
    "INDIA POST PAYMENTS BANK": "India Post Payments Bank",
    "FINO PAYMENTS BANK": "Fino Payments Bank",
    "JIO PAYMENTS BANK": "Jio Payments Bank",
    "NSDL PAYMENTS BANK": "NSDL Payments Bank",

    # Small Finance Banks
    "AU SMALL FINANCE BANK LIMITED": "AU Small Finance Bank",
    "AU SMALL FINANCE BANK LTD": "AU Small Finance Bank",
    "EQUITAS SMALL FINANCE BANK LIMITED": "Equitas Small Finance Bank",
    "EQUITAS SMALL FINANCE BANK LTD": "Equitas Small Finance Bank",
    "UJJIVAN SMALL FINANCE BANK LIMITED": "Ujjivan Small Finance Bank",
    "UJJIVAN SMALL FINANCE BANK LTD": "Ujjivan Small Finance Bank",
    "JANA SMALL FINANCE BANK LIMITED": "Jana Small Finance Bank",
    "JANA SMALL FINANCE BANK LTD": "Jana Small Finance Bank",
    "ESAF SMALL FINANCE BANK LIMITED": "ESAF Small Finance Bank",
    "ESAF SMALL FINANCE BANK LTD": "ESAF Small Finance Bank",
    "UTKARSH SMALL FINANCE BANK LIMITED": "Utkarsh Small Finance Bank",
    "UTKARSH SMALL FINANCE BANK LTD": "Utkarsh Small Finance Bank",
    "CAPITAL SMALL FINANCE BANK LIMITED": "Capital Small Finance Bank",
    "CAPITAL SMALL FINANCE BANK LTD": "Capital Small Finance Bank",
    "FINCARE SMALL FINANCE BANK LIMITED": "Fincare Small Finance Bank",
    "SURYODAY SMALL FINANCE BANK LIMITED": "Suryoday Small Finance Bank",
    "SURYODAY SMALL FINANCE BANK LTD": "Suryoday Small Finance Bank",
    "NORTH EAST SMALL FINANCE BANK LIMITED": "North East Small Finance Bank",
    "NORTH EAST SMALL FINANCE BANK LTD": "North East Small Finance Bank",
    "SHIVALIK SMALL FINANCE BANK LTD": "Shivalik Small Finance Bank",
    "UNITY SMALL FINANCE BANK LTD": "Unity Small Finance Bank",
}

# Merger Mapping: bank_name -> (anchor_bank, is_merged, merge_year)
MERGER_INFO = {
    "Allahabad Bank": ("Indian Bank", True, 2020),
    "Andhra Bank": ("Union Bank of India", True, 2020),
    "Corporation Bank": ("Union Bank of India", True, 2020),
    "Oriental Bank of Commerce": ("Punjab National Bank", True, 2020),
    "United Bank of India": ("Punjab National Bank", True, 2020),
    "Syndicate Bank": ("Canara Bank", True, 2020),
    "Laxmi Vilas Bank": ("DBS Bank", True, 2020),
    "Citi Bank": ("Axis Bank", True, 2023),
}

# Sector / Category Classification
BANK_CATEGORY_MAP = {
    # Public
    "State Bank of India": ("Public Sector", "Public"),
    "Punjab National Bank": ("Public Sector", "Public"),
    "Bank of Baroda": ("Public Sector", "Public"),
    "Canara Bank": ("Public Sector", "Public"),
    "Union Bank of India": ("Public Sector", "Public"),
    "Bank of India": ("Public Sector", "Public"),
    "Indian Bank": ("Public Sector", "Public"),
    "Central Bank of India": ("Public Sector", "Public"),
    "Indian Overseas Bank": ("Public Sector", "Public"),
    "UCO Bank": ("Public Sector", "Public"),
    "Bank of Maharashtra": ("Public Sector", "Public"),
    "Punjab & Sind Bank": ("Public Sector", "Public"),
    "IDBI Bank": ("Public Sector", "Public"),
    "Allahabad Bank": ("Public Sector", "Public"),
    "Andhra Bank": ("Public Sector", "Public"),
    "Corporation Bank": ("Public Sector", "Public"),
    "Oriental Bank of Commerce": ("Public Sector", "Public"),
    "United Bank of India": ("Public Sector", "Public"),
    "Syndicate Bank": ("Public Sector", "Public"),

    # Private
    "HDFC Bank": ("Private Sector", "Private"),
    "ICICI Bank": ("Private Sector", "Private"),
    "Axis Bank": ("Private Sector", "Private"),
    "Kotak Mahindra Bank": ("Private Sector", "Private"),
    "IndusInd Bank": ("Private Sector", "Private"),
    "Yes Bank": ("Private Sector", "Private"),
    "Federal Bank": ("Private Sector", "Private"),
    "IDFC First Bank": ("Private Sector", "Private"),
    "Bandhan Bank": ("Private Sector", "Private"),
    "RBL Bank": ("Private Sector", "Private"),
    "South Indian Bank": ("Private Sector", "Private"),
    "City Union Bank": ("Private Sector", "Private"),
    "Karur Vysya Bank": ("Private Sector", "Private"),
    "Karnataka Bank": ("Private Sector", "Private"),
    "Tamilnad Mercantile Bank": ("Private Sector", "Private"),
    "DCB Bank": ("Private Sector", "Private"),
    "Dhanlaxmi Bank": ("Private Sector", "Private"),
    "CSB Bank": ("Private Sector", "Private"),
    "J&K Bank": ("Private Sector", "Private"),
    "Laxmi Vilas Bank": ("Private Sector", "Private"),
    "Nainital Bank": ("Private Sector", "Private"),

    # Foreign
    "Citi Bank": ("Foreign Banks", "Foreign"),
    "Standard Chartered Bank": ("Foreign Banks", "Foreign"),
    "HSBC": ("Foreign Banks", "Foreign"),
    "American Express": ("Foreign Banks", "Foreign"),
    "DBS Bank": ("Foreign Banks", "Foreign"),
    "Deutsche Bank": ("Foreign Banks", "Foreign"),
    "Barclays Bank": ("Foreign Banks", "Foreign"),
    "Bank of America": ("Foreign Banks", "Foreign"),
    "Doha Bank": ("Foreign Banks", "Foreign"),
    "SBM Bank": ("Foreign Banks", "Foreign"),
    "Woori Bank": ("Foreign Banks", "Foreign"),
    "KEB Hana Bank": ("Foreign Banks", "Foreign"),
    "Kookmin Bank": ("Foreign Banks", "Foreign"),
    "Bank of Bahrain & Kuwait": ("Foreign Banks", "Foreign"),

    # Payments Banks
    "Paytm Payments Bank": ("Payment Banks", "Payments Bank"),
    "Airtel Payments Bank": ("Payment Banks", "Payments Bank"),
    "India Post Payments Bank": ("Payment Banks", "Payments Bank"),
    "Fino Payments Bank": ("Payment Banks", "Payments Bank"),
    "Jio Payments Bank": ("Payment Banks", "Payments Bank"),
    "NSDL Payments Bank": ("Payment Banks", "Payments Bank"),

    # Small Finance Banks
    "AU Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Equitas Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Ujjivan Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Jana Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "ESAF Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Utkarsh Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Capital Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Fincare Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Suryoday Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "North East Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Shivalik Small Finance Bank": ("Small Finance Banks", "Small Finance"),
    "Unity Small Finance Bank": ("Small Finance Banks", "Small Finance"),
}


def to_num(val):
    """Clean string number into float."""
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip().replace(',', '').replace(' ', '')
    if not s or s == '-' or s == 'NA' or s == 'NIL' or s == 'nil':
        return 0.0
    try:
        return float(s)
    except:
        return 0.0


def normalize_bank_name(raw_name):
    """Normalize messy raw bank names."""
    if not raw_name:
        return ""
    name_clean = str(raw_name).strip().upper()
    name_clean = re.sub(r'^\d+\s*', '', name_clean)  # Strip leading numbers
    name_clean = name_clean.replace('.', '').strip()

    # Direct match in dict
    for k, v in BANK_NORMALIZE.items():
        if k.replace('.', '').upper() == name_clean:
            return v

    # Fuzzy/Substring match
    for k, v in BANK_NORMALIZE.items():
        k_clean = k.replace('.', '').upper()
        if k_clean in name_clean or name_clean in k_clean:
            return v

    # Fallback to Title Cased
    return raw_name.strip().title()


def parse_raw_file(filepath):
    """Parse one raw CSV and extract standardized transaction records."""
    df = pd.read_csv(filepath, dtype=str)
    if df.empty:
        return []

    year = int(df['year'].iloc[0])
    month = int(df['month'].iloc[0])

    records = []
    for _, row in df.iterrows():
        raw_vals = [row.get(f'raw_col_{i}', '') for i in range(1, len(df.columns) - 2)]
        raw_vals = ["" if pd.isna(v) else str(v).strip() for v in raw_vals]

        # Filter out empty or header-only rows
        if not raw_vals or not any(raw_vals):
            continue

        # Check if first col is serial number or bank name
        c0 = raw_vals[0]
        if c0.isdigit() and len(raw_vals) > 1 and not raw_vals[1].replace('.', '').isdigit():
            # c0 is Sr No, c1 is Bank Name
            raw_bank = raw_vals[1]
            data_cols = raw_vals[2:]
        else:
            raw_bank = raw_vals[0]
            data_cols = raw_vals[1:]

        # Skip headers / totals / footnote rows
        if not raw_bank or raw_bank.upper() in ['TOTAL', 'TOTAL NUMBER', 'BANK NAME', 'SUB TOTAL']:
            continue
        raw_upper = raw_bank.upper()
        if any(h in raw_upper for h in [
            'SCHEDULED COMMERCIAL', 'PUBLIC SECTOR', 'PRIVATE SECTOR', 'FOREIGN BANKS',
            'TOTAL NUMBER', 'TOTAL VALUE', 'FINANCIAL TRANSACTIONS', 'OUTSTANDING CARDS',
            'NUMBER OF', 'VALUE OF', 'TRANSACTIONS DONE', 'NOTE', 'PROVISIONAL',
            'CARDS WITHDRAWAN', 'CARDS WITHDRAWN', 'CASH WITHDRAWAL TRANSACTIONS',
            'E-COMMERCE SITES', 'POS TERMINALS', 'MAIL-ORDER'
        ]):
            continue

        bank_name = normalize_bank_name(raw_bank)
        if not bank_name or len(bank_name) < 2:
            continue

        # Extract metrics based on format regime
        # Regime 3: 2022-03 onwards (>= 25 data cols)
        if len(data_cols) >= 25:
            # 1: On-site ATM, 2: Off-site ATM, 3: PoS, 4: Micro ATM, 5: Bharat QR, 6: UPI QR
            # 7: CC Outstanding, 8: DC Outstanding
            # 9: CC PoS vol, 10: CC PoS val ('000), 11: CC E-com vol, 12: CC E-com val ('000)
            # 13: CC Other vol, 14: CC Other val ('000), 15: CC ATM vol, 16: CC ATM val ('000)
            # 17: DC PoS vol, 18: DC PoS val ('000), 19: DC E-com vol, 20: DC E-com val ('000)
            # 21: DC Other vol, 22: DC Other val ('000), 23: DC ATM vol, 24: DC ATM val ('000)
            # 25: DC PoS Cash vol, 26: DC PoS Cash val ('000)
            atm_onsite = to_num(data_cols[0])
            atm_offsite = to_num(data_cols[1])
            pos_terminals = to_num(data_cols[2])
            micro_atms = to_num(data_cols[3])
            bharat_qr = to_num(data_cols[4])
            upi_qr = to_num(data_cols[5])
            cc_outstanding = to_num(data_cols[6])
            dc_outstanding = to_num(data_cols[7])

            cc_pos_vol = to_num(data_cols[8])
            cc_pos_val_k = to_num(data_cols[9])
            cc_ecom_vol = to_num(data_cols[10])
            cc_ecom_val_k = to_num(data_cols[11])
            cc_atm_vol = to_num(data_cols[14])
            cc_atm_val_k = to_num(data_cols[15])

            dc_pos_vol = to_num(data_cols[16])
            dc_pos_val_k = to_num(data_cols[17])
            dc_ecom_vol = to_num(data_cols[18])
            dc_ecom_val_k = to_num(data_cols[19])
            dc_atm_vol = to_num(data_cols[22])
            dc_atm_val_k = to_num(data_cols[23])

            # Convert '000 to Lakh (1 Lakh = 100,000 = 100 * thousand)
            cc_atm_value_lakh = round(cc_atm_val_k / 100.0, 2)
            cc_pos_value_lakh = round((cc_pos_val_k + cc_ecom_val_k) / 100.0, 2)
            dc_atm_value_lakh = round(dc_atm_val_k / 100.0, 2)
            dc_pos_value_lakh = round((dc_pos_val_k + dc_ecom_val_k) / 100.0, 2)

            cc_pos_total_vol = cc_pos_vol + cc_ecom_vol
            dc_pos_total_vol = dc_pos_vol + dc_ecom_vol

        # Regime 2: 2020-05 to 2022-02 (~16-17 data cols, includes Micro ATMs at index 4)
        elif len(data_cols) >= 16:
            atm_onsite = to_num(data_cols[0])
            atm_offsite = to_num(data_cols[1])
            pos_terminals = to_num(data_cols[2])  # Online PoS
            micro_atms = to_num(data_cols[4])
            bharat_qr = 0.0
            upi_qr = 0.0
            cc_outstanding = to_num(data_cols[6])
            cc_atm_vol = to_num(data_cols[7])
            cc_pos_total_vol = to_num(data_cols[8])
            cc_atm_value_lakh = to_num(data_cols[9])
            cc_pos_value_lakh = to_num(data_cols[10])

            dc_outstanding = to_num(data_cols[11])
            dc_atm_vol = to_num(data_cols[12])
            dc_pos_total_vol = to_num(data_cols[13])
            dc_atm_value_lakh = to_num(data_cols[14])
            dc_pos_value_lakh = to_num(data_cols[15])

        # Regime 1: 2020-01 to 2020-04 (14 data cols, no Micro ATMs)
        else:
            atm_onsite = to_num(data_cols[0]) if len(data_cols) > 0 else 0.0
            atm_offsite = to_num(data_cols[1]) if len(data_cols) > 1 else 0.0
            pos_terminals = to_num(data_cols[2]) if len(data_cols) > 2 else 0.0
            micro_atms = 0.0
            bharat_qr = 0.0
            upi_qr = 0.0
            cc_outstanding = to_num(data_cols[4]) if len(data_cols) > 4 else 0.0
            cc_atm_vol = to_num(data_cols[5]) if len(data_cols) > 5 else 0.0
            cc_pos_total_vol = to_num(data_cols[6]) if len(data_cols) > 6 else 0.0
            cc_atm_value_lakh = to_num(data_cols[7]) if len(data_cols) > 7 else 0.0
            cc_pos_value_lakh = to_num(data_cols[8]) if len(data_cols) > 8 else 0.0

            dc_outstanding = to_num(data_cols[9]) if len(data_cols) > 9 else 0.0
            dc_atm_vol = to_num(data_cols[10]) if len(data_cols) > 10 else 0.0
            dc_pos_total_vol = to_num(data_cols[11]) if len(data_cols) > 11 else 0.0
            dc_atm_value_lakh = to_num(data_cols[12]) if len(data_cols) > 12 else 0.0
            dc_pos_value_lakh = to_num(data_cols[13]) if len(data_cols) > 13 else 0.0

        # Anchor bank and merger status
        if bank_name in MERGER_INFO:
            anchor_bank, is_merged, merge_year = MERGER_INFO[bank_name]
        else:
            anchor_bank = bank_name
            is_merged = False
            merge_year = None

        # Category and Sector
        category_name, sector = BANK_CATEGORY_MAP.get(bank_name, ("Private Sector", "Private"))

        # Reporting check
        total_activity = sum([
            atm_onsite, atm_offsite, pos_terminals, cc_outstanding, dc_outstanding,
            cc_atm_vol, cc_pos_total_vol, dc_atm_vol, dc_pos_total_vol
        ])
        is_reported = total_activity > 0

        records.append({
            "year": year,
            "month": month,
            "bank_name": bank_name,
            "bank_category": category_name,
            "sector": sector,
            "anchor_bank": anchor_bank,
            "is_merged": is_merged,
            "merge_year": merge_year if is_merged else 0,
            "atm_onsite_count": int(atm_onsite),
            "atm_offsite_count": int(atm_offsite),
            "atm_total_count": int(atm_onsite + atm_offsite),
            "pos_online_count": int(pos_terminals),
            "micro_atm_count": int(micro_atms),
            "credit_cards_outstanding": int(cc_outstanding),
            "credit_txn_atm_vol": int(cc_atm_vol),
            "credit_txn_pos_vol": int(cc_pos_total_vol),
            "credit_txn_atm_value_lakh": round(cc_atm_value_lakh, 2),
            "credit_txn_pos_value_lakh": round(cc_pos_value_lakh, 2),
            "credit_txn_total_value_lakh": round(cc_atm_value_lakh + cc_pos_value_lakh, 2),
            "debit_cards_outstanding": int(dc_outstanding),
            "debit_txn_atm_vol": int(dc_atm_vol),
            "debit_txn_pos_vol": int(dc_pos_total_vol),
            "debit_txn_atm_value_lakh": round(dc_atm_value_lakh, 2),
            "debit_txn_pos_value_lakh": round(dc_pos_value_lakh, 2),
            "debit_txn_total_value_lakh": round(dc_atm_value_lakh + dc_pos_value_lakh, 2),
            "is_reported": is_reported
        })

    return records


def run_etl():
    """Execute end-to-end cleaning on all 60 monthly CSVs."""
    os.makedirs(CLEANED_DIR, exist_ok=True)
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "atm_*.csv")))
    print(f"Found {len(raw_files)} raw CSV files in {RAW_DIR}")

    all_records = []
    for fp in raw_files:
        fn = os.path.basename(fp)
        try:
            recs = parse_raw_file(fp)
            all_records.extend(recs)
        except Exception as e:
            print(f"Error processing {fn}: {e}")

    df_cleaned = pd.DataFrame(all_records)
    
    # Sort for consistency
    df_cleaned.sort_values(by=["year", "month", "bank_category", "bank_name"], inplace=True)
    df_cleaned.reset_index(drop=True, inplace=True)

    df_cleaned.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"\nETL completed successfully!")
    print(f"Saved master cleaned dataset to: {OUTPUT_CSV}")
    print(f"Total records: {len(df_cleaned)}")
    print(f"Unique banks: {df_cleaned['bank_name'].nunique()}")
    print(f"Years covered: {sorted(df_cleaned['year'].unique())}")
    print(f"Categories: {df_cleaned['bank_category'].value_counts().to_dict()}")

    return df_cleaned


if __name__ == "__main__":
    run_etl()

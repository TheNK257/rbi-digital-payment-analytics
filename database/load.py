"""
Data Warehouse Loader for RBI Payment Analytics
Loads cleaned_transactions.csv into:
1. MySQL Database (Star Schema: Fact_Transaction, Dim_Date, Dim_Bank, Dim_BankCategory, Dim_Channel)
2. Normalized Star Schema CSVs in database/star_schema_tables/ (ready for instant Power BI import)
3. SQLite local data warehouse (database/rbi_banking_bi.db) as local mirror
"""

import os
import sys
import sqlite3
import pandas as pd
import pymysql

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_CSV = os.path.join(BASE_DIR, "cleaned_data", "cleaned_transactions.csv")
SCHEMA_SQL = os.path.join(BASE_DIR, "database", "schema.sql")
TABLES_DIR = os.path.join(BASE_DIR, "database", "star_schema_tables")
SQLITE_DB = os.path.join(BASE_DIR, "database", "rbi_banking_bi.db")

# Default MySQL configuration (can be overridden via environment variables or .env)
DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_PORT = int(os.environ.get("MYSQL_PORT", 3306))
DB_USER = os.environ.get("MYSQL_USER", "root")
DB_PASS = os.environ.get("MYSQL_PASSWORD", "")
DB_NAME = os.environ.get("MYSQL_DATABASE", "rbi_banking_bi")

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def build_star_schema_dataframes(df_raw):
    """Transform flat cleaned transactions into relational star schema DataFrames."""
    print("Building Star Schema relational dimensions and facts...")

    # 1. Dim_Date
    dates = df_raw[['year', 'month']].drop_duplicates().sort_values(by=['year', 'month']).reset_index(drop=True)
    dim_date_rows = []
    for _, r in dates.iterrows():
        y = int(r['year'])
        m = int(r['month'])
        date_key = y * 100 + m
        m_name = MONTH_NAMES[m]
        q = f"Q{(m - 1) // 3 + 1}"
        fy = f"FY{y - 1}-{str(y)[-2:]}" if m <= 3 else f"FY{y}-{str(y + 1)[-2:]}"
        dim_date_rows.append({
            "date_key": date_key,
            "year": y,
            "month": m,
            "month_name": m_name,
            "quarter": q,
            "fiscal_year": fy
        })
    df_dim_date = pd.DataFrame(dim_date_rows)

    # 2. Dim_Bank
    banks = df_raw[['bank_name', 'anchor_bank', 'is_merged', 'merge_year']].drop_duplicates(subset=['bank_name']).sort_values(by=['bank_name']).reset_index(drop=True)
    banks['bank_key'] = range(1, len(banks) + 1)
    df_dim_bank = banks[['bank_key', 'bank_name', 'anchor_bank', 'is_merged', 'merge_year']]
    bank_map = dict(zip(df_dim_bank['bank_name'], df_dim_bank['bank_key']))

    # 3. Dim_BankCategory
    cats = df_raw[['bank_category', 'sector']].drop_duplicates().sort_values(by=['bank_category']).reset_index(drop=True)
    cats['category_key'] = range(1, len(cats) + 1)
    cats.rename(columns={'bank_category': 'category_name'}, inplace=True)
    df_dim_category = cats[['category_key', 'category_name', 'sector']]
    cat_map = dict(zip(df_dim_category['category_name'], df_dim_category['category_key']))

    # 4. Dim_Channel
    channel_rows = [
        {"channel_key": 1, "channel_name": "ATM", "channel_type": "Physical Infrastructure", "is_digital": False},
        {"channel_key": 2, "channel_name": "POS Terminal", "channel_type": "Merchant Acceptance", "is_digital": True},
        {"channel_key": 3, "channel_name": "Online / E-Commerce", "channel_type": "Digital Remote", "is_digital": True},
        {"channel_key": 4, "channel_name": "Micro ATM & QR", "channel_type": "Agent & QR Network", "is_digital": True}
    ]
    df_dim_channel = pd.DataFrame(channel_rows)

    # 5. Fact_Transaction
    fact_rows = []
    for idx, r in df_raw.iterrows():
        y = int(r['year'])
        m = int(r['month'])
        date_key = y * 100 + m
        b_name = r['bank_name']
        c_name = r['bank_category']

        b_key = bank_map.get(b_name, 1)
        c_key = cat_map.get(c_name, 1)

        fact_rows.append({
            "txn_id": idx + 1,
            "date_key": date_key,
            "bank_key": b_key,
            "category_key": c_key,
            "channel_key": 1,  # Default multi-channel composite
            "atm_onsite_count": int(r['atm_onsite_count']),
            "atm_offsite_count": int(r['atm_offsite_count']),
            "atm_total_count": int(r['atm_total_count']),
            "pos_online_count": int(r['pos_online_count']),
            "micro_atm_count": int(r['micro_atm_count']),
            "credit_cards_outstanding": int(r['credit_cards_outstanding']),
            "debit_cards_outstanding": int(r['debit_cards_outstanding']),
            "credit_txn_atm_vol": int(r['credit_txn_atm_vol']),
            "credit_txn_pos_vol": int(r['credit_txn_pos_vol']),
            "credit_txn_atm_value_lakh": float(r['credit_txn_atm_value_lakh']),
            "credit_txn_pos_value_lakh": float(r['credit_txn_pos_value_lakh']),
            "credit_txn_total_value_lakh": float(r['credit_txn_total_value_lakh']),
            "debit_txn_atm_vol": int(r['debit_txn_atm_vol']),
            "debit_txn_pos_vol": int(r['debit_txn_pos_vol']),
            "debit_txn_atm_value_lakh": float(r['debit_txn_atm_value_lakh']),
            "debit_txn_pos_value_lakh": float(r['debit_txn_pos_value_lakh']),
            "debit_txn_total_value_lakh": float(r['debit_txn_total_value_lakh']),
            "is_reported": bool(r['is_reported'])
        })

    df_fact = pd.DataFrame(fact_rows)

    return df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact


def export_csv_tables(df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact):
    """Export separate CSV files for each Star Schema table for Power BI import."""
    os.makedirs(TABLES_DIR, exist_ok=True)
    df_dim_date.to_csv(os.path.join(TABLES_DIR, "Dim_Date.csv"), index=False)
    df_dim_bank.to_csv(os.path.join(TABLES_DIR, "Dim_Bank.csv"), index=False)
    df_dim_category.to_csv(os.path.join(TABLES_DIR, "Dim_BankCategory.csv"), index=False)
    df_dim_channel.to_csv(os.path.join(TABLES_DIR, "Dim_Channel.csv"), index=False)
    df_fact.to_csv(os.path.join(TABLES_DIR, "Fact_Transaction.csv"), index=False)
    print(f"Exported all 5 Star Schema CSV tables to: {TABLES_DIR}")


def load_to_sqlite(df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact):
    """Load dimensional model into local SQLite database."""
    conn = sqlite3.connect(SQLITE_DB)
    df_dim_date.to_sql("Dim_Date", conn, if_exists="replace", index=False)
    df_dim_bank.to_sql("Dim_Bank", conn, if_exists="replace", index=False)
    df_dim_category.to_sql("Dim_BankCategory", conn, if_exists="replace", index=False)
    df_dim_channel.to_sql("Dim_Channel", conn, if_exists="replace", index=False)
    df_fact.to_sql("Fact_Transaction", conn, if_exists="replace", index=False)

    # Verification query
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.bank_name, SUM(f.credit_cards_outstanding) as total_cc
        FROM Fact_Transaction f
        JOIN Dim_Bank b ON f.bank_key = b.bank_key
        JOIN Dim_Date d ON f.date_key = d.date_key
        WHERE d.year = 2024
        GROUP BY b.bank_name
        ORDER BY total_cc DESC
        LIMIT 5;
    """)
    top_banks = cursor.fetchall()
    conn.close()
    print(f"Loaded Star Schema into SQLite: {SQLITE_DB}")
    print("Verification Query (Top 5 Credit Card Banks 2024):", top_banks)


def load_to_mysql(df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact, password=""):
    """Load dimensional model into MySQL server."""
    print(f"Attempting to connect to MySQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"MySQL connection failed: {e}")
        return False

    with conn.cursor() as cursor:
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS rbi_banking_bi CHARACTER SET utf8mb4;")
        cursor.execute("USE rbi_banking_bi;")
        
        # Read and run schema DDL
        with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
            sql_statements = f.read().split(";")
            for stmt in sql_statements:
                clean_stmt = stmt.strip()
                if clean_stmt:
                    cursor.execute(clean_stmt)
        print("MySQL Star Schema tables created successfully.")

        # Insert Dim_Date
        print("Inserting Dim_Date rows...")
        for _, r in df_dim_date.iterrows():
            cursor.execute("""
                INSERT INTO Dim_Date (date_key, year, month, month_name, quarter, fiscal_year)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (int(r['date_key']), int(r['year']), int(r['month']), r['month_name'], r['quarter'], r['fiscal_year']))

        # Insert Dim_Bank
        print("Inserting Dim_Bank rows...")
        for _, r in df_dim_bank.iterrows():
            cursor.execute("""
                INSERT INTO Dim_Bank (bank_key, bank_name, anchor_bank, is_merged, merge_year)
                VALUES (%s, %s, %s, %s, %s)
            """, (int(r['bank_key']), r['bank_name'], r['anchor_bank'], bool(r['is_merged']), int(r['merge_year']) if r['merge_year'] else None))

        # Insert Dim_BankCategory
        print("Inserting Dim_BankCategory rows...")
        for _, r in df_dim_category.iterrows():
            cursor.execute("""
                INSERT INTO Dim_BankCategory (category_key, category_name, sector)
                VALUES (%s, %s, %s)
            """, (int(r['category_key']), r['category_name'], r['sector']))

        # Insert Dim_Channel
        print("Inserting Dim_Channel rows...")
        for _, r in df_dim_channel.iterrows():
            cursor.execute("""
                INSERT INTO Dim_Channel (channel_key, channel_name, channel_type, is_digital)
                VALUES (%s, %s, %s, %s)
            """, (int(r['channel_key']), r['channel_name'], r['channel_type'], bool(r['is_digital'])))

        # Insert Fact_Transaction in batches of 500
        print(f"Inserting Fact_Transaction rows ({len(df_fact)} records)...")
        batch_size = 500
        fact_tuples = [
            (
                int(r['date_key']), int(r['bank_key']), int(r['category_key']), int(r['channel_key']),
                int(r['atm_onsite_count']), int(r['atm_offsite_count']), int(r['atm_total_count']),
                int(r['pos_online_count']), int(r['micro_atm_count']),
                int(r['credit_cards_outstanding']), int(r['debit_cards_outstanding']),
                int(r['credit_txn_atm_vol']), int(r['credit_txn_pos_vol']),
                float(r['credit_txn_atm_value_lakh']), float(r['credit_txn_pos_value_lakh']), float(r['credit_txn_total_value_lakh']),
                int(r['debit_txn_atm_vol']), int(r['debit_txn_pos_vol']),
                float(r['debit_txn_atm_value_lakh']), float(r['debit_txn_pos_value_lakh']), float(r['debit_txn_total_value_lakh']),
                bool(r['is_reported'])
            )
            for _, r in df_fact.iterrows()
        ]

        insert_sql = """
            INSERT INTO Fact_Transaction (
                date_key, bank_key, category_key, channel_key,
                atm_onsite_count, atm_offsite_count, atm_total_count,
                pos_online_count, micro_atm_count,
                credit_cards_outstanding, debit_cards_outstanding,
                credit_txn_atm_vol, credit_txn_pos_vol,
                credit_txn_atm_value_lakh, credit_txn_pos_value_lakh, credit_txn_total_value_lakh,
                debit_txn_atm_vol, debit_txn_pos_vol,
                debit_txn_atm_value_lakh, debit_txn_pos_value_lakh, debit_txn_total_value_lakh,
                is_reported
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for i in range(0, len(fact_tuples), batch_size):
            cursor.executemany(insert_sql, fact_tuples[i:i + batch_size])
        
        conn.commit()

        # Run verification query
        cursor.execute("""
            SELECT b.bank_name, SUM(f.credit_cards_outstanding) as total_cc
            FROM Fact_Transaction f
            JOIN Dim_Bank b ON f.bank_key = b.bank_key
            JOIN Dim_Date d ON f.date_key = d.date_key
            WHERE d.year = 2024
            GROUP BY b.bank_name
            ORDER BY total_cc DESC
            LIMIT 5;
        """)
        top_mysql = cursor.fetchall()
        print("MySQL Verification Query Result (Top 5 Credit Card Banks 2024):", top_mysql)

    conn.close()
    return True


def main():
    if not os.path.exists(CLEANED_CSV):
        print(f"Error: Cleaned transactions CSV not found at {CLEANED_CSV}")
        return

    print(f"Reading cleaned dataset from {CLEANED_CSV}...")
    df_raw = pd.read_csv(CLEANED_CSV)

    df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact = build_star_schema_dataframes(df_raw)

    # 1. Export CSV tables for direct Power BI drag-and-drop / Folder import
    export_csv_tables(df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact)

    # 2. Load into local SQLite mirror
    load_to_sqlite(df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact)

    # 3. Try MySQL load if password is provided or prompt
    password = DB_PASS or (sys.argv[1] if len(sys.argv) > 1 else "")
    if password:
        load_to_mysql(df_dim_date, df_dim_bank, df_dim_category, df_dim_channel, df_fact, password=password)
    else:
        print("\nNote: MySQL password not provided via argument or env var.")
        print("To load directly into MySQL, run: python database/load.py <your_mysql_password>")


if __name__ == "__main__":
    main()

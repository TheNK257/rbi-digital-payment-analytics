"""
RBI ATM/POS/Card Statistics Scraper
Scrapes 60 months of bank-wise payment statistics from RBI (Jan 2020 - Dec 2024).
Generates 60 raw CSV files in ../raw_data/
"""

import os
import sys
import time
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

START_ATMID = 107  # January 2020
END_ATMID = 166    # December 2024 (Total 60 months)
BASE_URL = "https://www.rbi.org.in/Scripts/ATMView.aspx?atmid={}"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw_data")

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

CATEGORY_KEYWORDS = [
    "Scheduled Commercial Banks",
    "Public Sector Banks",
    "Private Sector Banks",
    "Foreign Banks",
    "Payment Banks",
    "Payments Bank",
    "Small Finance Banks"
]


def extract_year_month(soup, atmid):
    """Derive year and month from page heading or fallback to atmid arithmetic."""
    month_offset = atmid - START_ATMID
    calc_year = 2020 + (month_offset // 12)
    calc_month = 1 + (month_offset % 12)

    # Attempt to confirm from title text
    text = soup.get_text()
    for y in range(2020, 2026):
        for m_idx, m_name in enumerate(MONTH_NAMES, start=1):
            pattern = rf'{m_name}\s*[-–,\s]\s*{y}'
            if re.search(pattern, text, re.IGNORECASE):
                return y, m_idx

    return calc_year, calc_month


def scrape_month(atmid, session=None):
    """Scrape a single month ATMView page and return raw rows and metadata."""
    url = BASE_URL.format(atmid)
    s = session or requests.Session()
    
    for attempt in range(3):
        try:
            resp = s.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                break
            time.sleep(2)
        except Exception as e:
            if attempt == 2:
                raise e
            time.sleep(2)

    soup = BeautifulSoup(resp.text, 'html.parser')
    year, month = extract_year_month(soup, atmid)

    tables = soup.find_all('table', class_='tablebg')
    if not tables:
        raise ValueError(f"No tablebg found on page for atmid={atmid}")

    data_table = tables[-1]
    raw_rows = []
    
    current_category = "General"
    for tr in data_table.find_all('tr'):
        cells = [c.get_text().strip().replace('\xa0', ' ') for c in tr.find_all(['td', 'th'])]
        if not cells or not any(cells):
            continue

        # Check if row is a section header (e.g. Public Sector Banks)
        combined_text = " ".join(cells).strip()
        matched_cat = False
        for cat in CATEGORY_KEYWORDS:
            if cat.lower() in combined_text.lower() and len(cells) <= 3:
                current_category = cat
                matched_cat = True
                break
        if matched_cat:
            continue

        # Skip table title / subheaders with purely column numbers or labels
        if 'Bank Name' in cells or 'ATM & Card Statistics' in combined_text or 'ATM, Acceptance Infrastructure' in combined_text:
            continue
        if any(c in ['On-site', 'Off-site', 'Credit Cards', 'Debit Cards'] for c in cells[:4]):
            continue
        if all(c.isdigit() or c == '' for c in cells):
            continue
        if combined_text.startswith("Note") or combined_text.startswith("Total number of"):
            continue

        # Store raw row with category tag and atmid metadata
        raw_rows.append([year, month, current_category] + cells)

    return year, month, raw_rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    session = requests.Session()
    print(f"Starting RBI Scraper for 60 months (atmid {START_ATMID} to {END_ATMID})...")
    print(f"Destination: {OUTPUT_DIR}")

    success_count = 0
    for atmid in range(START_ATMID, END_ATMID + 1):
        month_offset = atmid - START_ATMID
        exp_year = 2020 + (month_offset // 12)
        exp_month = 1 + (month_offset % 12)
        target_file = os.path.join(OUTPUT_DIR, f"atm_{exp_year}_{exp_month:02d}.csv")

        # Skip if already exists and non-empty
        if os.path.exists(target_file) and os.path.getsize(target_file) > 500:
            print(f"[{atmid}/{END_ATMID}] {exp_year}-{exp_month:02d} already downloaded, skipping.")
            success_count += 1
            continue

        try:
            year, month, rows = scrape_month(atmid, session)
            if not rows:
                print(f"Warning: No rows parsed for atmid={atmid} ({year}-{month:02d})")
                continue

            max_len = max(len(r) for r in rows)
            # Pad rows to equal length
            padded_rows = [r + [''] * (max_len - len(r)) for r in rows]
            
            # Base header columns
            col_names = ["year", "month", "scraped_category"] + [f"raw_col_{i}" for i in range(1, max_len - 2)]
            df = pd.DataFrame(padded_rows, columns=col_names)
            df.to_csv(target_file, index=False, encoding='utf-8')
            print(f"[{atmid}/{END_ATMID}] Saved {target_file} ({len(df)} rows, {len(df.columns)} cols)")
            success_count += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Error scraping atmid={atmid}: {e}")

    print(f"\nScraping complete! {success_count}/60 files saved in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

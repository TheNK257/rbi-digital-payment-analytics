"""
Generate Reference Chart Visualizations for the 6 Power BI KPIs.
Saves PNG charts into dashboard/visual_previews/ to guide Power BI dashboard creation.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "cleaned_data", "cleaned_transactions.csv")
PREVIEW_DIR = os.path.join(BASE_DIR, "dashboard", "visual_previews")
os.makedirs(PREVIEW_DIR, exist_ok=True)

df = pd.read_csv(DATA_CSV)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# Visual 1: ATM count trend - Public vs Private
fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
df_atm = df[df['bank_category'].isin(['Public Sector', 'Private Sector'])]
pvt_pub = df_atm.groupby(['year', 'month', 'bank_category'])['atm_total_count'].sum().unstack()
pvt_pub.index = [f"{y}-{m:02d}" for y, m in pvt_pub.index]
pvt_pub.plot(ax=ax, color=['#005b96', '#f37735'], linewidth=2.5)
ax.set_title("Visual 1: ATM Deployment Trend — Public vs. Private Sector (2020–2024)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Year-Month", fontsize=11)
ax.set_ylabel("Total ATMs Deployed", fontsize=11)
ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
plt.xticks(rotation=45)
plt.tight_layout()
fig.savefig(os.path.join(PREVIEW_DIR, "visual_1_atm_trend.png"))
plt.close(fig)

# Visual 2: Top 10 banks by credit cards outstanding (2024)
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
df_2024 = df[df['year'] == 2024]
top10_cc = df_2024.groupby('bank_name')['credit_cards_outstanding'].max().sort_values(ascending=True).tail(10)
top10_cc.plot(kind='barh', ax=ax, color='#1d3557')
ax.set_title("Visual 2: Top 10 Banks by Credit Card Circulation (2024 Peak)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Outstanding Credit Cards", fontsize=11)
ax.set_ylabel("Bank Entity", fontsize=11)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x*1e-6:.1f}M'))
plt.tight_layout()
fig.savefig(os.path.join(PREVIEW_DIR, "visual_2_top10_credit_cards.png"))
plt.close(fig)

# Visual 3: POS terminal growth - Public vs Private
fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
pos_growth = df_atm.groupby(['year', 'bank_category'])['pos_online_count'].sum().unstack()
pos_growth.plot(kind='bar', ax=ax, color=['#0077b6', '#ffb703'], width=0.7)
ax.set_title("Visual 3: Merchant PoS Terminal Growth by Sector (2020–2024)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Year", fontsize=11)
ax.set_ylabel("Total Active PoS Terminals", fontsize=11)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x*1e-6:.1f}M'))
plt.xticks(rotation=0)
plt.tight_layout()
fig.savefig(os.path.join(PREVIEW_DIR, "visual_3_pos_growth.png"))
plt.close(fig)

# Visual 4: Debit card ATM vs POS volume
fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
dc_vol = df.groupby('year')[['debit_txn_atm_vol', 'debit_txn_pos_vol']].sum()
dc_vol_pct = dc_vol.div(dc_vol.sum(axis=1), axis=0) * 100
dc_vol_pct.plot(kind='bar', stacked=True, ax=ax, color=['#6c757d', '#2a9d8f'], width=0.6)
ax.set_title("Visual 4: Debit Card Structural Shift — Cash Withdrawal vs. POS/E-Com (%)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Year", fontsize=11)
ax.set_ylabel("Transaction Volume Share (%)", fontsize=11)
ax.legend(["ATM Cash Withdrawal", "POS / E-Commerce Purchase"], loc='upper right')
plt.xticks(rotation=0)
plt.tight_layout()
fig.savefig(os.path.join(PREVIEW_DIR, "visual_4_debit_usage_shift.png"))
plt.close(fig)

# Visual 5: Monthly transaction value heatmap
fig, ax = plt.subplots(figsize=(11, 4.5), dpi=150)
heatmap_data = df.groupby(['bank_category', 'month'])['credit_txn_pos_value_lakh'].sum().unstack()
month_abbr = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
heatmap_data.columns = [month_abbr[m-1] for m in heatmap_data.columns]
im = ax.imshow(heatmap_data.values, cmap='YlGnBu', aspect='auto')
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns, fontsize=10)
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index, fontsize=10)
ax.set_title("Visual 5: Credit Card POS Spending Heatmap (Seasonal Surge in Q3-Q4)", fontsize=13, fontweight='bold', pad=12)
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('Total Value (INR Lakh)', fontsize=10)
plt.tight_layout()
fig.savefig(os.path.join(PREVIEW_DIR, "visual_5_spending_heatmap.png"))
plt.close(fig)

# Visual 6: Pre/post merger bank volume continuity
fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
merged_df = df[df['anchor_bank'].isin(['Indian Bank', 'Union Bank of India', 'Punjab National Bank', 'Canara Bank'])]
merger_trends = merged_df.groupby(['year', 'anchor_bank'])['atm_total_count'].sum().unstack()
merger_trends.plot(ax=ax, marker='o', linewidth=2.2)
ax.set_title("Visual 6: Post-Merger Anchor Bank Infrastructure Continuity (2020–2024)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Year", fontsize=11)
ax.set_ylabel("Total ATMs Maintained", fontsize=11)
plt.xticks(range(2020, 2025))
plt.tight_layout()
fig.savefig(os.path.join(PREVIEW_DIR, "visual_6_merger_continuity.png"))
plt.close(fig)

print("Generated all 6 reference chart mockups in dashboard/visual_previews/")

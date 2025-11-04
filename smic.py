#!/usr/bin/env python3
"""
SMIC Portfolio: Realistic Drift Model
Starts 100% Vanguard ETFs on 2024-08-27
Each stock purchase = swap ETF → stock (same $ amount, same day)
After swap, sector weights drift naturally based on relative performance
(Time-dependent weights, no rebalancing - realistic implementation)
"""

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import os

plt.style.use('bmh')

# Ensure output directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('figs', exist_ok=True)

# Load data
try:
    df = pd.read_csv('data/transactions.csv', parse_dates=['invest_date'])
    if df.empty:
        raise ValueError("Transaction data file is empty")
    required_columns = ['sector', 'ticker', 'invest_date', 'amount_invested']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    print(f"Loaded {len(df)} transactions from data/transactions.csv")
except FileNotFoundError:
    raise FileNotFoundError("Transaction data file not found: data/transactions.csv")
except Exception as e:
    raise RuntimeError(f"Error loading transaction data: {str(e)}")
V = {'Technology': 'VGT', 'Healthcare': 'VHT', 'Financials': 'VFH',
     'Consumer_Discretionary': 'VCR', 'Communication_Services': 'VOX',
     'Industrials': 'VIS', 'Consumer_Staples': 'VDC',
     'Energy': 'VDE', 'Materials': 'VAW', 'Real_Estate': 'VNQ',
     'Utilities': 'VPU'}

# Sector name mapping
sector_map = {
    'Technology': 'Technology',
    'Healthcare': 'Healthcare',
    'Financials': 'Financials',
    'Consumer_Discretionary': 'Consumer_Discretionary',
    'Communication_Services': 'Communication_Services',
    'Industrials': 'Industrials',
    'Consumer_Staples': 'Consumer_Staples',
    'Energy': 'Energy',
    'Materials': 'Materials',
    'Real_Estate': 'Real_Estate',
    'Utilities': 'Utilities'
}

# Determine start date (first portfolio investment date)
start_date = df['invest_date'].min()
print(f"Portfolio start date: {start_date.date()}")

# Download prices
all_tickers = list(set(df['ticker'].tolist()) | set(V.values()) | {'^GSPC'})
print(f"Downloading price data for {len(all_tickers)} tickers...")
try:
    px = yf.download(all_tickers, start=start_date - pd.Timedelta(days=10), end='2025-11-05',
                     progress=False, auto_adjust=False)['Adj Close'].asfreq('B').ffill()
    if px.empty:
        raise ValueError("No price data downloaded")
    print(f"Downloaded price data: {len(px)} trading days")
except Exception as e:
    raise RuntimeError(f"Error downloading price data: {str(e)}")

# Find the nearest trading day to start_date
start_idx = px.index.get_indexer([pd.Timestamp(start_date)], method='nearest')[0]
actual_start = px.index[start_idx]
print(f"Actual trading start date: {actual_start.date()}")

# Filter to start from portfolio start date
px = px.loc[actual_start:]

# Initialize units
units = pd.DataFrame(0.0, index=px.index, columns=px.columns)

# Process each position
df_sorted = df.sort_values('invest_date')
for _, row in df_sorted.iterrows():
    try:
        dt_idx = px.index.get_indexer([pd.Timestamp(row['invest_date'])], method='nearest')[0]
        dt = px.index[dt_idx]
    except:
        dt = px.index[px.index.get_loc(pd.Timestamp(row['invest_date']), method='nearest')]
    
    ticker = row['ticker']
    sector = row['sector']
    usd = row['amount_invested']
    shares = row.get('shares', 0)  # Get shares from CSV, default to 0 if column missing
    
    # --- FIX 1: SKIP CASH ---
    # Cash is handled separately, so we skip its transaction row
    if sector == 'Cash' or ticker == 'CASH':
        continue
        
    # Validation checks
    if pd.isna(usd) or usd <= 0:
        print(f"WARNING: Invalid amount_invested for {ticker} on {row['invest_date']}: {usd}")
        continue
    
    if ticker not in px.columns:
        print(f"WARNING: Ticker {ticker} not found in price data, skipping")
        continue

    # --- FIX 2: USE 'shares' COLUMN ---
    # Initial ETFs or Fixed Income
    if ticker in V.values() or sector == 'Fixed_Income':
        if shares > 0:
            units.loc[dt:, ticker] += shares
        else:
            # Fallback if 'shares' column is missing/zero
            units.loc[dt:, ticker] += usd / px.loc[dt, ticker]

    # Stock purchase = swap from ETF
    else:
        # Map sector to ETF (simplified mapping)
        sector_key = sector_map.get(sector)
        if not sector_key:
            sec_clean = sector.replace('_', ' ')
            if sec_clean in V:
                sector_key = sec_clean
            else:
                first = sector.split('_')[0]
                for v_key in V.keys():
                    if v_key.startswith(first):
                        sector_key = v_key
                        break
        
        if sector_key and sector_key in V:
            etf = V[sector_key]
            if etf in px.columns:
                etf_price = px.loc[dt, etf]
                
                # 1. Buy stock (using 'shares' from CSV)
                if shares > 0:
                    units.loc[dt:, ticker] += shares
                else:
                    # Fallback if 'shares' column is missing/zero
                    stock_price = px.loc[dt, ticker]
                    if not (pd.isna(stock_price) or stock_price <= 0):
                        units.loc[dt:, ticker] += usd / stock_price
                    else:
                        print(f"WARNING: Invalid stock price for {ticker} on {dt}")
                        continue
                
                # 2. Sell ETF (using dollar amount)
                if not (pd.isna(etf_price) or etf_price <= 0):
                    units.loc[dt:, etf] -= usd / etf_price
                else:
                    print(f"WARNING: Invalid ETF price for {etf} on {dt}, cannot sell")

units = units.ffill().fillna(0)

# --- FIX 3: ADD CASH TO TOTAL PORTFOLIO VALUE ---

# 1. Get the static cash value from transactions
cash_val = df[df['sector'] == 'Cash']['amount_invested'].sum()
print(f"\nStatic cash balance: ${cash_val:,.2f}")

# 2. Calculate the value of *invested* assets
invested_value = (units * px).sum(axis=1)

# 3. Create the *true* total portfolio value
portfolio_value = invested_value + cash_val
print(f"Initial Total Portfolio Value: ${portfolio_value.iloc[0]:,.2f}")

# Validation: Check for negative portfolio values
if (portfolio_value < 0).any():
    print("WARNING: Some portfolio values are negative, this may indicate data issues")
    negative_days = portfolio_value[portfolio_value < 0]
    print(f"Negative values found on {len(negative_days)} days")

# Validation: Check for zero or missing portfolio values
if (portfolio_value <= 0).any():
    raise ValueError("Portfolio value is zero or negative, cannot calculate weights")

# Calculate cumulative returns (percentage from start)
initial_value = portfolio_value.iloc[0]
portfolio_cumulative_return = (portfolio_value / initial_value - 1) * 100

# Benchmark (S&P 500, normalized to match portfolio's initial value)
benchmark_px = px['^GSPC']
benchmark_value = (benchmark_px / benchmark_px.iloc[0]) * initial_value
benchmark_cumulative_return = (benchmark_value / initial_value - 1) * 100

# Calculate sector weights (only when portfolio has value)
weights = pd.DataFrame(index=px.index)

for sector_name, v_key in sector_map.items():
    if v_key in V:
        etf = V[v_key]
        tickers = df[df['sector'] == sector_name]['ticker'].tolist()
        sector_value = units[etf] * px[etf]
        for t in tickers:
            if t in units.columns and t in px.columns and t != etf:
                sector_value += units[t] * px[t]
        # Calculate weights, handling division by zero
        weights[sector_name] = (sector_value / portfolio_value * 100).fillna(0)

# Fixed Income
fi_tickers = df[df['sector'] == 'Fixed_Income']['ticker'].tolist()
fi_value = pd.Series(0.0, index=px.index)
for t in fi_tickers:
    if t in units.columns and t in px.columns:
        fi_value += units[t] * px[t]
weights['Fixed Income'] = (fi_value / portfolio_value * 100).fillna(0)

# Cash (constant) - already calculated above, just use it for weights
weights['Cash'] = (cash_val / portfolio_value * 100).fillna(0)

# Replace any inf or nan with 0
weights = weights.replace([float('inf'), float('-inf')], 0).fillna(0)

# Sort sectors by final weight (largest to smallest), with Cash at bottom
final_weights = weights.iloc[-1].sort_values(ascending=False)
# Separate equity sectors, Fixed Income, and Cash
equity_sectors = [s for s in final_weights.index if s not in ['Fixed Income', 'Cash']]
sorted_equity = sorted(equity_sectors, key=lambda x: final_weights[x], reverse=True)
column_order = sorted_equity + ['Fixed Income', 'Cash']
# Only include columns that exist
column_order = [c for c in column_order if c in weights.columns]
weights = weights[column_order]

# Track weight drift over time
print(f"\nWeights DataFrame: {weights.shape[0]} rows, {weights.shape[1]} columns")
if weights.shape[0] > 0:
    total_first = weights.sum(axis=1).iloc[0]
    total_last = weights.sum(axis=1).iloc[-1]
    print(f"Total weight sum (first day): {total_first:.1f}%")
    print(f"Total weight sum (last day): {total_last:.1f}%")
    # Normalize to 100% if needed (small rounding errors)
    if abs(total_last - 100) > 1:
        weights = weights.div(weights.sum(axis=1), axis=0) * 100
        print(f"Normalized weights to ensure 100% total")

# Results
initial = portfolio_value.iloc[0]
final = portfolio_value.iloc[-1]
benchmark_initial = benchmark_value.iloc[0]
benchmark_final = benchmark_value.iloc[-1]

# Calculate time period
days = (portfolio_value.index[-1] - portfolio_value.index[0]).days
years = days / 365.25
months = days / 30.44

# Calculate returns
total_return = (final / initial - 1) * 100
benchmark_total_return = (benchmark_final / benchmark_initial - 1) * 100
cagr = ((final / initial) ** (1 / years) - 1) * 100
benchmark_cagr = ((benchmark_final / benchmark_initial) ** (1 / years) - 1) * 100

# Calculate initial sector weights
initial_weights = pd.Series(index=weights.columns)
for sec in weights.columns:
    initial_weights[sec] = weights[sec].iloc[0]

# Calculate absolute and percentage changes
absolute_change = final - initial
benchmark_absolute_change = benchmark_final - benchmark_initial

# Print comprehensive report
print("\n" + "="*70)
print("SMIC PORTFOLIO PERFORMANCE REPORT")
print("="*70)

print(f"\n{'PERIOD SUMMARY':^70}")
print("-"*70)
print(f"Start Date:        {portfolio_value.index[0].strftime('%Y-%m-%d')}")
print(f"End Date:          {portfolio_value.index[-1].strftime('%Y-%m-%d')}")
print(f"Duration:          {days} days ({months:.1f} months / {years:.2f} years)")

print(f"\n{'PORTFOLIO VALUES':^70}")
print("-"*70)
print(f"Initial Value:     ${initial:>15,.2f}")
print(f"Final Value:       ${final:>15,.2f}")
print(f"Absolute Change:   ${absolute_change:>15,.2f}")
print(f"Total Return:      {total_return:>15.2f}%")

print(f"\n{'S&P 500 BENCHMARK':^70}")
print("-"*70)
print(f"Initial Value:     ${benchmark_initial:>15,.2f}")
print(f"Final Value:       ${benchmark_final:>15,.2f}")
print(f"Absolute Change:   ${benchmark_absolute_change:>15,.2f}")
print(f"Total Return:      {benchmark_total_return:>15.2f}%")

print(f"\n{'ANNUALIZED RETURNS':^70}")
print("-"*70)
print(f"Portfolio CAGR:    {cagr:>15.2f}%")
print(f"S&P 500 CAGR:      {benchmark_cagr:>15.2f}%")
print(f"Outperformance:    {(cagr - benchmark_cagr):>15.2f}%")

print(f"\n{'SECTOR ALLOCATION - BEGINNING':^70}")
print("-"*70)
for sec in weights.columns:
    print(f"  {sec:25s} {initial_weights[sec]:>6.2f}%")

print(f"\n{'SECTOR ALLOCATION - END':^70}")
print("-"*70)
weight_changes = []
for sec in weights.columns:
    end_weight = weights[sec].iloc[-1]
    change = end_weight - initial_weights[sec]
    pct_change = (change / initial_weights[sec] * 100) if initial_weights[sec] > 0 else 0
    weight_changes.append({
        'sector': sec,
        'initial': initial_weights[sec],
        'final': end_weight,
        'absolute_change': change,
        'pct_change': pct_change
    })
    print(f"  {sec:25s} {end_weight:>6.2f}%  ({change:+.2f}% absolute, {pct_change:+.1f}% relative)")

print(f"\n{'WEIGHT DRIFT ANALYSIS':^70}")
print("-"*70)
# Sort by absolute change
weight_changes_sorted = sorted(weight_changes, key=lambda x: abs(x['absolute_change']), reverse=True)
print("Sectors with largest absolute weight changes:")
for i, wc in enumerate(weight_changes_sorted[:5], 1):
    direction = "↑" if wc['absolute_change'] > 0 else "↓"
    print(f"  {i}. {wc['sector']:25s} {direction} {abs(wc['absolute_change']):>5.2f}% "
          f"(from {wc['initial']:>5.2f}% to {wc['final']:>5.2f}%)")

print(f"\n{'SECTOR ALLOCATION CHANGES':^70}")
print("-"*70)
sector_changes = []
for sec in weights.columns:
    change = weights[sec].iloc[-1] - initial_weights[sec]
    sector_changes.append((sec, change))
sector_changes.sort(key=lambda x: abs(x[1]), reverse=True)
for sec, change in sector_changes:
    if abs(change) > 0.01:
        print(f"  {sec:25s} {change:>+7.2f}%")

print(f"\n{'PORTFOLIO STATISTICS':^70}")
print("-"*70)
max_value = portfolio_value.max()
max_date = portfolio_value.idxmax()
min_value = portfolio_value.min()
min_date = portfolio_value.idxmin()
max_drawdown = ((portfolio_value / portfolio_value.expanding().max()) - 1).min() * 100

print(f"Peak Value:        ${max_value:>15,.2f}  ({max_date.strftime('%Y-%m-%d')})")
print(f"Lowest Value:      ${min_value:>15,.2f}  ({min_date.strftime('%Y-%m-%d')})")
print(f"Max Drawdown:      {max_drawdown:>15.2f}%")

print(f"\n{'COMPOSITION SUMMARY':^70}")
print("-"*70)
equity_weight_start = sum([initial_weights[s] for s in weights.columns if s not in ['Fixed Income', 'Cash']])
equity_weight_end = sum([weights[s].iloc[-1] for s in weights.columns if s not in ['Fixed Income', 'Cash']])
fi_weight_start = initial_weights.get('Fixed Income', 0)
fi_weight_end = weights['Fixed Income'].iloc[-1] if 'Fixed Income' in weights.columns else 0
cash_weight_start = initial_weights.get('Cash', 0)
cash_weight_end = weights['Cash'].iloc[-1] if 'Cash' in weights.columns else 0

print(f"Equity Allocation:")
print(f"  Beginning:       {equity_weight_start:>15.2f}%")
print(f"  Ending:          {equity_weight_end:>15.2f}%")
print(f"  Change:          {(equity_weight_end - equity_weight_start):>+15.2f}%")
print(f"\nFixed Income Allocation:")
print(f"  Beginning:       {fi_weight_start:>15.2f}%")
print(f"  Ending:          {fi_weight_end:>15.2f}%")
print(f"  Change:          {(fi_weight_end - fi_weight_start):>+15.2f}%")
print(f"\nCash Allocation:")
print(f"  Beginning:       {cash_weight_start:>15.2f}%")
print(f"  Ending:          {cash_weight_end:>15.2f}%")
print(f"  Change:          {(cash_weight_end - cash_weight_start):>+15.2f}%")

print("\n" + "="*70)

# Export statistics summary to CSV
summary_data = {
    'Metric': [
        'Start Date', 'End Date', 'Duration (days)', 'Duration (years)',
        'Initial Portfolio Value', 'Final Portfolio Value', 'Absolute Change', 'Total Return (%)',
        'Initial S&P 500 Value', 'Final S&P 500 Value', 'S&P 500 Absolute Change', 'S&P 500 Total Return (%)',
        'Portfolio CAGR (%)', 'S&P 500 CAGR (%)', 'Outperformance (%)',
        'Peak Value', 'Peak Date', 'Lowest Value', 'Lowest Date', 'Max Drawdown (%)',
        'Equity Allocation Start (%)', 'Equity Allocation End (%)', 'Equity Change (%)',
        'Fixed Income Start (%)', 'Fixed Income End (%)', 'Fixed Income Change (%)',
        'Cash Start (%)', 'Cash End (%)', 'Cash Change (%)'
    ],
    'Value': [
        portfolio_value.index[0].strftime('%Y-%m-%d'),
        portfolio_value.index[-1].strftime('%Y-%m-%d'),
        str(days),
        f'{years:.2f}',
        f'${initial:,.2f}',
        f'${final:,.2f}',
        f'${absolute_change:,.2f}',
        f'{total_return:.2f}',
        f'${benchmark_initial:,.2f}',
        f'${benchmark_final:,.2f}',
        f'${benchmark_absolute_change:,.2f}',
        f'{benchmark_total_return:.2f}',
        f'{cagr:.2f}',
        f'{benchmark_cagr:.2f}',
        f'{(cagr - benchmark_cagr):.2f}',
        f'${max_value:,.2f}',
        max_date.strftime('%Y-%m-%d'),
        f'${min_value:,.2f}',
        min_date.strftime('%Y-%m-%d'),
        f'{max_drawdown:.2f}',
        f'{equity_weight_start:.2f}',
        f'{equity_weight_end:.2f}',
        f'{(equity_weight_end - equity_weight_start):.2f}',
        f'{fi_weight_start:.2f}',
        f'{fi_weight_end:.2f}',
        f'{(fi_weight_end - fi_weight_start):.2f}',
        f'{cash_weight_start:.2f}',
        f'{cash_weight_end:.2f}',
        f'{(cash_weight_end - cash_weight_start):.2f}'
    ]
}
summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('data/smic_statistics_summary.csv', index=False)
print(f"\nStatistics summary exported: data/smic_statistics_summary.csv")

# Export sector weights over time to CSV
weights_export = weights.copy()
weights_export['Date'] = weights_export.index
weights_export = weights_export[['Date'] + [col for col in weights.columns]]
weights_export.to_csv('data/smic_sector_weights.csv', index=False)
print(f"Sector weights exported: data/smic_sector_weights.csv")

# Calculate ETF vs Individual Stocks weights for each sector (YTD)
sector_etf_stocks = pd.DataFrame(index=px.index)

for sector_name, v_key in sector_map.items():
    if v_key in V:
        etf = V[v_key]
        
        # ETF value for this sector
        etf_value = units[etf] * px[etf] if etf in units.columns and etf in px.columns else pd.Series(0.0, index=px.index)
        
        # Individual stocks value for this sector
        tickers = df[df['sector'] == sector_name]['ticker'].tolist()
        stocks_value = pd.Series(0.0, index=px.index)
        for t in tickers:
            if t in units.columns and t in px.columns and t != etf:
                stocks_value += units[t] * px[t]
        
        # Total sector value
        sector_total = etf_value + stocks_value
        
        # Calculate weights as percentage of total portfolio
        etf_weight = (etf_value / portfolio_value * 100).fillna(0)
        stocks_weight = (stocks_value / portfolio_value * 100).fillna(0)
        
        sector_etf_stocks[f'{sector_name}_ETF'] = etf_weight
        sector_etf_stocks[f'{sector_name}_Stocks'] = stocks_weight

# Export ETF vs Stocks comparison
etf_stocks_export = sector_etf_stocks.copy()
etf_stocks_export['Date'] = etf_stocks_export.index
cols = ['Date'] + [col for col in sector_etf_stocks.columns]
etf_stocks_export = etf_stocks_export[cols]
etf_stocks_export.to_csv('data/smic_etf_vs_stocks_weights.csv', index=False)
print(f"ETF vs Stocks weights exported: data/smic_etf_vs_stocks_weights.csv")

# Create YTD summary by sector (ETF vs Stocks)
ytd_summary = []
for sector_name, v_key in sector_map.items():
    if v_key in V:
        etf_col = f'{sector_name}_ETF'
        stocks_col = f'{sector_name}_Stocks'
        
        if etf_col in sector_etf_stocks.columns and stocks_col in sector_etf_stocks.columns:
            # Get first and last values
            etf_start = sector_etf_stocks[etf_col].iloc[0]
            etf_end = sector_etf_stocks[etf_col].iloc[-1]
            stocks_start = sector_etf_stocks[stocks_col].iloc[0]
            stocks_end = sector_etf_stocks[stocks_col].iloc[-1]
            
            # Calculate changes
            etf_change = etf_end - etf_start
            stocks_change = stocks_end - stocks_start
            
            # Total sector weight
            sector_start = etf_start + stocks_start
            sector_end = etf_end + stocks_end
            sector_change = sector_end - sector_start
            
            ytd_summary.append({
                'Sector': sector_name,
                'ETF_Weight_Start (%)': round(etf_start, 2),
                'ETF_Weight_End (%)': round(etf_end, 2),
                'ETF_Change (%)': round(etf_change, 2),
                'Stocks_Weight_Start (%)': round(stocks_start, 2),
                'Stocks_Weight_End (%)': round(stocks_end, 2),
                'Stocks_Change (%)': round(stocks_change, 2),
                'Total_Sector_Start (%)': round(sector_start, 2),
                'Total_Sector_End (%)': round(sector_end, 2),
                'Total_Sector_Change (%)': round(sector_change, 2)
            })

ytd_df = pd.DataFrame(ytd_summary)
ytd_df.to_csv('data/smic_sector_etf_vs_stocks_ytd.csv', index=False)
print(f"Sector ETF vs Stocks YTD summary exported: data/smic_sector_etf_vs_stocks_ytd.csv")

# Print YTD summary
print(f"\n{'SECTOR ETF vs STOCKS - YTD SUMMARY':^70}")
print("-"*70)
print(f"{'Sector':<25} {'ETF End':>10} {'Stocks End':>12} {'Total':>10}")
print("-"*70)
for _, row in ytd_df.iterrows():
    print(f"{row['Sector']:<25} {row['ETF_Weight_End (%)']:>9.2f}% {row['Stocks_Weight_End (%)']:>11.2f}% {row['Total_Sector_End (%)']:>9.2f}%")

# Plot - Sector Allocation (smic_results.png)
fig, ax = plt.subplots(1, 1, figsize=(16, 10))

# Define unique color palette for sectors (distinct colors)
sector_colors = {
    'Technology': '#1f77b4',           # Blue
    'Financials': '#ff7f0e',           # Orange
    'Consumer_Discretionary': '#2ca02c', # Green
    'Communication_Services': '#d62728', # Red
    'Healthcare': '#9467bd',            # Purple
    'Industrials': '#8c564b',          # Brown
    'Consumer_Staples': '#e377c2',     # Pink
    'Energy': '#7f7f7f',                # Gray
    'Real_Estate': '#bcbd22',          # Olive
    'Materials': '#17becf',            # Cyan
    'Utilities': '#ffbb78',            # Peach
    'Fixed Income': '#98df8a',         # Light Green
    'Cash': '#ff9896'                  # Light Red
}

# Create color list matching column order
color_list = [sector_colors.get(col, '#808080') for col in weights.columns]

# Sector weights (stacked area chart) with percentage labels
weights.plot.area(ax=ax, alpha=0.75, linewidth=0, stacked=True, color=color_list)
ax.set_title('Sector Allocation', fontsize=18, fontweight='bold', pad=20)
ax.set_ylabel('Weight (%)', fontsize=14, fontweight='bold')
ax.set_xlabel('Date', fontsize=14, fontweight='bold')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3, linestyle='--')
ax.tick_params(axis='both', labelsize=12)

# Add percentage labels at the end of the period (no threshold - label all sectors)
y_pos = 0
for col in weights.columns:
    final_weight = weights[col].iloc[-1]
    if final_weight > 0:  # Label all sectors with any weight
        y_pos += final_weight / 2
        ax.text(weights.index[-1], y_pos, f'{final_weight:.1f}%', 
                fontsize=9, fontweight='bold', ha='left', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=0.5))
        y_pos += final_weight / 2

plt.tight_layout()
plt.savefig('figs/smic_results.png', dpi=300, bbox_inches='tight')
print(f"\nChart saved: figs/smic_results.png")

# Plot - Portfolio Value and Cumulative Returns
fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), sharex=True)

# Top panel: Portfolio Value Over Time (USD)
ax1.plot(portfolio_value.index, portfolio_value.values, 
         label='SMIC Portfolio', lw=3, color='#1f77b4')
ax1.plot(benchmark_value.index, benchmark_value.values, 
         label='S&P 500', lw=3, linestyle='--', color='#d62728', alpha=0.8)
ax1.set_title('Portfolio Value', fontsize=18, fontweight='bold', pad=20)
ax1.set_ylabel('USD', fontsize=14, fontweight='bold')
ax1.legend(fontsize=12, loc='upper left', frameon=True, fancybox=True, shadow=True)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.tick_params(axis='both', labelsize=12)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

# Bottom panel: Cumulative Returns (%)
ax2.plot(portfolio_cumulative_return.index, portfolio_cumulative_return.values, 
         label='SMIC Portfolio', lw=3, color='#1f77b4')
ax2.plot(benchmark_cumulative_return.index, benchmark_cumulative_return.values, 
         label='S&P 500', lw=3, linestyle='--', color='#d62728', alpha=0.8)
ax2.set_title('Cumulative Returns', fontsize=18, fontweight='bold', pad=20)
ax2.set_ylabel('Return (%)', fontsize=14, fontweight='bold')
ax2.set_xlabel('Date', fontsize=14, fontweight='bold')
ax2.legend(fontsize=12, loc='upper left', frameon=True, fancybox=True, shadow=True)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.tick_params(axis='both', labelsize=12)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.3)

plt.tight_layout()
plt.savefig('figs/smic_portfolio_performance.png', dpi=300, bbox_inches='tight')
print(f"Portfolio performance chart saved: figs/smic_portfolio_performance.png")

# Plot - ETF vs Stocks Breakdown
fig2, (ax4, ax5) = plt.subplots(2, 1, figsize=(16, 12), sharex=True)

# Top panel: ETF weights over time by sector
etf_cols = [col for col in sector_etf_stocks.columns if col.endswith('_ETF')]
etf_df = sector_etf_stocks[etf_cols].copy()
etf_df.columns = [col.replace('_ETF', '') for col in etf_df.columns]

# Use unique colors for ETF plot
etf_color_map = {col: sector_colors.get(col, '#808080') for col in etf_df.columns}
etf_colors_list = [etf_color_map[col] for col in etf_df.columns]
etf_df.plot.area(ax=ax4, alpha=0.75, linewidth=0, stacked=True, color=etf_colors_list)

# Add percentage labels at end (no threshold - label all sectors)
y_pos_etf = 0
for col in etf_df.columns:
    final_weight = etf_df[col].iloc[-1]
    if final_weight > 0:  # Label all sectors with any weight
        y_pos_etf += final_weight / 2
        ax4.text(etf_df.index[-1], y_pos_etf, f'{final_weight:.1f}%', 
                fontsize=9, fontweight='bold', ha='left', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=0.5))
        y_pos_etf += final_weight / 2

ax4.set_title('ETF Weights by Sector', fontsize=18, fontweight='bold', pad=20)
ax4.set_ylabel('Weight (%)', fontsize=14, fontweight='bold')
ax4.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10, frameon=True, fancybox=True, shadow=True)
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.tick_params(axis='both', labelsize=12)

# Bottom panel: Individual Stocks weights over time by sector
stocks_cols = [col for col in sector_etf_stocks.columns if col.endswith('_Stocks')]
stocks_df = sector_etf_stocks[stocks_cols].copy()
stocks_df.columns = [col.replace('_Stocks', '') for col in stocks_df.columns]

# Use unique colors for Stocks plot (shifted palette to avoid overlap)
stocks_color_map = {col: sector_colors.get(col, '#808080') for col in stocks_df.columns}
stocks_colors_list = [stocks_color_map[col] for col in stocks_df.columns]
stocks_df.plot.area(ax=ax5, alpha=0.75, linewidth=0, stacked=True, color=stocks_colors_list)

# Add percentage labels at end (no threshold - label all sectors)
y_pos_stocks = 0
for col in stocks_df.columns:
    final_weight = stocks_df[col].iloc[-1]
    if final_weight > 0:  # Label all sectors with any weight
        y_pos_stocks += final_weight / 2
        ax5.text(stocks_df.index[-1], y_pos_stocks, f'{final_weight:.1f}%', 
                fontsize=9, fontweight='bold', ha='left', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=0.5))
        y_pos_stocks += final_weight / 2

ax5.set_title('Individual Stocks Weights by Sector', fontsize=18, fontweight='bold', pad=20)
ax5.set_ylabel('Weight (%)', fontsize=14, fontweight='bold')
ax5.set_xlabel('Date', fontsize=14, fontweight='bold')
ax5.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10, frameon=True, fancybox=True, shadow=True)
ax5.grid(True, alpha=0.3, linestyle='--')
ax5.tick_params(axis='both', labelsize=12)

plt.tight_layout()
plt.savefig('figs/smic_etf_vs_stocks.png', dpi=300, bbox_inches='tight')
print(f"ETF vs Stocks chart saved: figs/smic_etf_vs_stocks.png")

# Plot - YTD Comparison Bar Chart
fig3, ax6 = plt.subplots(1, 1, figsize=(16, 10))

# Prepare data for grouped bar chart
sectors = ytd_df['Sector'].tolist()
etf_ends = ytd_df['ETF_Weight_End (%)'].tolist()
stocks_ends = ytd_df['Stocks_Weight_End (%)'].tolist()

x = np.arange(len(sectors))
width = 0.35

bars1 = ax6.bar(x - width/2, etf_ends, width, label='ETF', color='#2E86AB', alpha=0.8)
bars2 = ax6.bar(x + width/2, stocks_ends, width, label='Individual Stocks', color='#F18F01', alpha=0.8)

ax6.set_title('Sector Allocation: ETF vs Individual Stocks', 
              fontsize=18, fontweight='bold', pad=20)
ax6.set_ylabel('Weight (%)', fontsize=14, fontweight='bold')
ax6.set_xlabel('Sector', fontsize=14, fontweight='bold')
ax6.set_xticks(x)
ax6.set_xticklabels(sectors, rotation=45, ha='right', fontsize=11)
ax6.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
ax6.grid(True, alpha=0.3, linestyle='--', axis='y')
ax6.tick_params(axis='both', labelsize=12)

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if height > 0.5:  # Only label if significant
            ax6.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('figs/smic_etf_vs_stocks_comparison.png', dpi=300, bbox_inches='tight')
print(f"ETF vs Stocks comparison chart saved: figs/smic_etf_vs_stocks_comparison.png")

# Plot - Weight Drift Over Time (separate plot)
fig4, ax7 = plt.subplots(1, 1, figsize=(16, 8))
weight_drift = weights.copy()
for col in weight_drift.columns:
    if col in initial_weights:
        weight_drift[col] = weight_drift[col] - initial_weights[col]
    else:
        weight_drift[col] = 0

# Only plot sectors with meaningful drift
drift_to_plot = []
drift_colors = {}
for col in weight_drift.columns:
    max_drift = abs(weight_drift[col]).max()
    if max_drift > 0.5:  # Only show sectors with >0.5% drift
        drift_to_plot.append(col)
        drift_colors[col] = sector_colors.get(col, '#808080')

if drift_to_plot:
    for col in drift_to_plot:
        ax7.plot(weight_drift.index, weight_drift[col].values, 
                label=col, linewidth=2.5, alpha=0.8, color=drift_colors[col])
    ax7.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax7.set_title('Sector Weight Drift', fontsize=18, fontweight='bold', pad=20)
    ax7.set_ylabel('Weight Change (%)', fontsize=14, fontweight='bold')
    ax7.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax7.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11, 
               frameon=True, fancybox=True, shadow=True, ncol=1)
    ax7.grid(True, alpha=0.3, linestyle='--')
    ax7.tick_params(axis='both', labelsize=12)

plt.tight_layout()
plt.savefig('figs/smic_weight_drift.png', dpi=300, bbox_inches='tight')
print(f"Weight drift chart saved: figs/smic_weight_drift.png")

# Generate CURRENT_ALLOCATION.md report
print("\n" + "="*70)
print("GENERATING CURRENT_ALLOCATION.md")
print("="*70)

# Validation: Ensure ytd_df is not empty
if ytd_df.empty:
    raise ValueError("No sector data available to generate allocation report")

# Get end date for the report
end_date = portfolio_value.index[-1].strftime('%B %d, %Y')

# Calculate overall allocation
# Calculate equity from sum of all sector ETF+Stocks totals for accuracy
equity_weight_end = ytd_df['Total_Sector_End (%)'].sum()
fi_weight_end = weights['Fixed Income'].iloc[-1] if 'Fixed Income' in weights.columns else 0
cash_weight_end = weights['Cash'].iloc[-1] if 'Cash' in weights.columns else 0

# Validation: Check that equity + fixed income + cash ≈ 100%
total_check = equity_weight_end + fi_weight_end + cash_weight_end
if abs(total_check - 100) > 2:
    print(f"WARNING: Total allocation doesn't sum to 100%: {total_check:.2f}%")
    # Use weights DataFrame total as fallback for equity if discrepancy is large
    equity_weight_end = sum([weights[s].iloc[-1] for s in weights.columns if s not in ['Fixed Income', 'Cash']])

# Build sector breakdown table
# Use ETF+Stocks totals from ytd_df for consistency (they sum correctly)
sector_rows = []
for sector_name, v_key in sector_map.items():
    # Get ETF and stocks weights from ytd_df
    sector_row = ytd_df[ytd_df['Sector'] == sector_name]
    if not sector_row.empty:
        etf_weight = sector_row['ETF_Weight_End (%)'].iloc[0]
        stocks_weight = sector_row['Stocks_Weight_End (%)'].iloc[0]
        # Use total from ytd_df for consistency (ETF + Stocks)
        total_weight = sector_row['Total_Sector_End (%)'].iloc[0]
        # Format sector name for display
        display_name = sector_name.replace('_', ' ')
        sector_rows.append({
            'sector': display_name,
            'total': total_weight,
            'etf': etf_weight,
            'stocks': stocks_weight
        })

# Sort by total weight descending
sector_rows.sort(key=lambda x: x['total'], reverse=True)

# Validation: Check that sector_rows were populated
if not sector_rows:
    raise ValueError("No sector rows were populated for allocation report")

# Categorize sectors
etf_heavy = []
stock_heavy = []
balanced = []

for row in sector_rows:
    if row['etf'] > row['stocks']:
        etf_heavy.append(row)
    elif row['stocks'] > row['etf']:
        stock_heavy.append(row)
    else:
        balanced.append(row)

# Write the markdown file
try:
    with open('CURRENT_ALLOCATION.md', 'w') as f:
        f.write("# Current SMIC Portfolio Allocation\n\n")
        f.write(f"**As of End of Period ({end_date})**\n\n\n\n")
        
        f.write("## Overall Allocation\n\n\n\n")
        f.write(f"- **Total Equity Allocation**: {equity_weight_end:.2f}%\n\n")
        f.write(f"- **Fixed Income**: {fi_weight_end:.2f}%\n\n")
        f.write(f"- **Cash**: {cash_weight_end:.2f}%\n\n\n\n")
        
        f.write("## Sector Breakdown\n\n\n\n")
        f.write("| Sector | Total Weight | ETF Weight | Individual Stocks Weight |\n")
        f.write("|--------|-------------|------------|--------------------------|\n")
        
        for row in sector_rows:
            f.write(f"| **{row['sector']}** | {row['total']:.2f}% | {row['etf']:.2f}% | {row['stocks']:.2f}% |\n")
        
        f.write("\n\n\n## Key Observations\n\n\n\n")
        
        if etf_heavy:
            f.write("1. **ETF-Heavy Sectors** (ETF > Stocks):\n\n")
            for row in etf_heavy:
                f.write(f"   - {row['sector']}: {row['etf']:.2f}% ETF vs {row['stocks']:.2f}% Stocks\n\n")
        
        if stock_heavy:
            f.write("2. **Stock-Heavy Sectors** (Stocks > ETF):\n\n")
            for row in stock_heavy:
                f.write(f"   - {row['sector']}: {row['stocks']:.2f}% Stocks vs {row['etf']:.2f}% ETF\n\n")
        
        if balanced:
            f.write("3. **Balanced Sectors**:\n\n")
            for row in balanced:
                f.write(f"   - {row['sector']}: {row['stocks']:.2f}% Stocks vs {row['etf']:.2f}% ETF\n\n")
        
        f.write("\n\n## Sector Analysis Files\n\n\n\n")
        f.write("Detailed analysis for each sector is available in:\n")
        f.write("- `sectors/[Sector_Name]/sector_performance.png` - Performance comparison (full period & YTD)\n\n")
        f.write("- `sectors/[Sector_Name]/sector_weights_and_returns.png` - Weights over time & YTD returns\n")
except Exception as e:
    raise RuntimeError(f"Error writing CURRENT_ALLOCATION.md: {str(e)}")

print(f"Allocation report saved: CURRENT_ALLOCATION.md")

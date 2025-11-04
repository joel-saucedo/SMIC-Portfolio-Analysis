#!/usr/bin/env python3
"""
SMIC Portfolio Analysis Core Module
Refactored for GUI integration - returns data and Plotly figures
"""

import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from typing import Tuple, Dict, List
import warnings
warnings.filterwarnings('ignore')

# Ensure output directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('figs', exist_ok=True)

# Vanguard ETF mappings
V = {
    'Technology': 'VGT', 'Healthcare': 'VHT', 'Financials': 'VFH',
    'Consumer_Discretionary': 'VCR', 'Communication_Services': 'VOX',
    'Industrials': 'VIS', 'Consumer_Staples': 'VDC',
    'Energy': 'VDE', 'Materials': 'VAW', 'Real_Estate': 'VNQ',
    'Utilities': 'VPU'
}

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

# Sector colors for consistent styling
SECTOR_COLORS = {
    'Technology': '#1f77b4',
    'Financials': '#ff7f0e',
    'Consumer_Discretionary': '#2ca02c',
    'Communication_Services': '#d62728',
    'Healthcare': '#9467bd',
    'Industrials': '#8c564b',
    'Consumer_Staples': '#e377c2',
    'Energy': '#7f7f7f',
    'Real_Estate': '#bcbd22',
    'Materials': '#17becf',
    'Utilities': '#ffbb78',
    'Fixed Income': '#98df8a',
    'Cash': '#ff9896'
}


def generate_portfolio_analysis(transactions_file: str = 'data/transactions.csv') -> Tuple[str, Dict, pd.DataFrame, pd.DataFrame]:
    """
    Main analysis function - generates portfolio analysis and returns results
    
    Returns:
        report_text (str): Formatted text report
        figures (dict): Dictionary of Plotly figure objects
        summary_df (pd.DataFrame): Statistics summary
        ytd_df (pd.DataFrame): YTD sector breakdown
    """
    
    # Load data
    try:
        df = pd.read_csv(transactions_file, parse_dates=['invest_date'])
        if df.empty:
            raise ValueError("Transaction data file is empty")
        required_columns = ['sector', 'ticker', 'invest_date', 'amount_invested']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Transaction data file not found: {transactions_file}")
    except Exception as e:
        raise RuntimeError(f"Error loading transaction data: {str(e)}")
    
    # Determine start date
    start_date = df['invest_date'].min()
    
    # Download prices
    all_tickers = list(set(df['ticker'].tolist()) | set(V.values()) | {'^GSPC'})
    try:
        px = yf.download(all_tickers, start=start_date - pd.Timedelta(days=10), end='2025-11-05',
                         progress=False, auto_adjust=False)['Adj Close'].asfreq('B').ffill()
        if px.empty:
            raise ValueError("No price data downloaded")
    except Exception as e:
        raise RuntimeError(f"Error downloading price data: {str(e)}")
    
    # Find the nearest trading day
    start_idx = px.index.get_indexer([pd.Timestamp(start_date)], method='nearest')[0]
    actual_start = px.index[start_idx]
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
        shares = row.get('shares', 0)
        
        # Skip cash - handled separately
        if sector == 'Cash' or ticker == 'CASH':
            continue
            
        if pd.isna(usd) or usd <= 0:
            continue
        
        if ticker not in px.columns:
            continue

        # Initial ETFs or Fixed Income
        if ticker in V.values() or sector == 'Fixed_Income':
            if shares > 0:
                units.loc[dt:, ticker] += shares
            else:
                units.loc[dt:, ticker] += usd / px.loc[dt, ticker]

        # Stock purchase = swap from ETF
        else:
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
                    
                    # Buy stock
                    if shares > 0:
                        units.loc[dt:, ticker] += shares
                    else:
                        stock_price = px.loc[dt, ticker]
                        if not (pd.isna(stock_price) or stock_price <= 0):
                            units.loc[dt:, ticker] += usd / stock_price
                        else:
                            continue
                    
                    # Sell ETF
                    if not (pd.isna(etf_price) or etf_price <= 0):
                        units.loc[dt:, etf] -= usd / etf_price

    units = units.ffill().fillna(0)
    
    # Add cash to portfolio value
    cash_val = df[df['sector'] == 'Cash']['amount_invested'].sum()
    invested_value = (units * px).sum(axis=1)
    portfolio_value = invested_value + cash_val
    
    if (portfolio_value <= 0).any():
        raise ValueError("Portfolio value is zero or negative, cannot calculate weights")
    
    # Calculate returns
    initial_value = portfolio_value.iloc[0]
    portfolio_cumulative_return = (portfolio_value / initial_value - 1) * 100
    
    # Benchmark
    benchmark_px = px['^GSPC']
    benchmark_value = (benchmark_px / benchmark_px.iloc[0]) * initial_value
    benchmark_cumulative_return = (benchmark_value / initial_value - 1) * 100
    
    # Calculate sector weights
    weights = pd.DataFrame(index=px.index)
    
    for sector_name, v_key in sector_map.items():
        if v_key in V:
            etf = V[v_key]
            tickers = df[df['sector'] == sector_name]['ticker'].tolist()
            sector_value = units[etf] * px[etf]
            for t in tickers:
                if t in units.columns and t in px.columns and t != etf:
                    sector_value += units[t] * px[t]
            weights[sector_name] = (sector_value / portfolio_value * 100).fillna(0)
    
    # Fixed Income
    fi_tickers = df[df['sector'] == 'Fixed_Income']['ticker'].tolist()
    fi_value = pd.Series(0.0, index=px.index)
    for t in fi_tickers:
        if t in units.columns and t in px.columns:
            fi_value += units[t] * px[t]
    weights['Fixed Income'] = (fi_value / portfolio_value * 100).fillna(0)
    
    # Cash
    weights['Cash'] = (cash_val / portfolio_value * 100).fillna(0)
    
    weights = weights.replace([float('inf'), float('-inf')], 0).fillna(0)
    
    # Sort sectors
    final_weights = weights.iloc[-1].sort_values(ascending=False)
    equity_sectors = [s for s in final_weights.index if s not in ['Fixed Income', 'Cash']]
    sorted_equity = sorted(equity_sectors, key=lambda x: final_weights[x], reverse=True)
    column_order = sorted_equity + ['Fixed Income', 'Cash']
    column_order = [c for c in column_order if c in weights.columns]
    weights = weights[column_order]
    
    # Normalize if needed
    total_last = weights.sum(axis=1).iloc[-1]
    if abs(total_last - 100) > 1:
        weights = weights.div(weights.sum(axis=1), axis=0) * 100
    
    # Calculate statistics
    initial = portfolio_value.iloc[0]
    final = portfolio_value.iloc[-1]
    benchmark_initial = benchmark_value.iloc[0]
    benchmark_final = benchmark_value.iloc[-1]
    
    days = (portfolio_value.index[-1] - portfolio_value.index[0]).days
    years = days / 365.25
    months = days / 30.44
    
    total_return = (final / initial - 1) * 100
    benchmark_total_return = (benchmark_final / benchmark_initial - 1) * 100
    cagr = ((final / initial) ** (1 / years) - 1) * 100
    benchmark_cagr = ((benchmark_final / benchmark_initial) ** (1 / years) - 1) * 100
    
    initial_weights = pd.Series(index=weights.columns)
    for sec in weights.columns:
        initial_weights[sec] = weights[sec].iloc[0]
    
    absolute_change = final - initial
    benchmark_absolute_change = benchmark_final - benchmark_initial
    
    max_value = portfolio_value.max()
    max_date = portfolio_value.idxmax()
    min_value = portfolio_value.min()
    min_date = portfolio_value.idxmin()
    max_drawdown = ((portfolio_value / portfolio_value.expanding().max()) - 1).min() * 100
    
    # Calculate ETF vs Stocks breakdown
    sector_etf_stocks = pd.DataFrame(index=px.index)
    
    for sector_name, v_key in sector_map.items():
        if v_key in V:
            etf = V[v_key]
            etf_value = units[etf] * px[etf] if etf in units.columns and etf in px.columns else pd.Series(0.0, index=px.index)
            tickers = df[df['sector'] == sector_name]['ticker'].tolist()
            stocks_value = pd.Series(0.0, index=px.index)
            for t in tickers:
                if t in units.columns and t in px.columns and t != etf:
                    stocks_value += units[t] * px[t]
            etf_weight = (etf_value / portfolio_value * 100).fillna(0)
            stocks_weight = (stocks_value / portfolio_value * 100).fillna(0)
            sector_etf_stocks[f'{sector_name}_ETF'] = etf_weight
            sector_etf_stocks[f'{sector_name}_Stocks'] = stocks_weight
    
    # Create YTD summary
    ytd_summary = []
    for sector_name, v_key in sector_map.items():
        if v_key in V:
            etf_col = f'{sector_name}_ETF'
            stocks_col = f'{sector_name}_Stocks'
            
            if etf_col in sector_etf_stocks.columns and stocks_col in sector_etf_stocks.columns:
                etf_start = sector_etf_stocks[etf_col].iloc[0]
                etf_end = sector_etf_stocks[etf_col].iloc[-1]
                stocks_start = sector_etf_stocks[stocks_col].iloc[0]
                stocks_end = sector_etf_stocks[stocks_col].iloc[-1]
                
                ytd_summary.append({
                    'Sector': sector_name,
                    'ETF_Weight_Start (%)': round(etf_start, 2),
                    'ETF_Weight_End (%)': round(etf_end, 2),
                    'ETF_Change (%)': round(etf_end - etf_start, 2),
                    'Stocks_Weight_Start (%)': round(stocks_start, 2),
                    'Stocks_Weight_End (%)': round(stocks_end, 2),
                    'Stocks_Change (%)': round(stocks_end - stocks_start, 2),
                    'Total_Sector_Start (%)': round(etf_start + stocks_start, 2),
                    'Total_Sector_End (%)': round(etf_end + stocks_end, 2),
                    'Total_Sector_Change (%)': round((etf_end + stocks_end) - (etf_start + stocks_start), 2)
                })
    
    ytd_df = pd.DataFrame(ytd_summary)
    
    # Generate report text
    report_lines = []
    report_lines.append("="*70)
    report_lines.append("SMIC PORTFOLIO PERFORMANCE REPORT")
    report_lines.append("="*70)
    report_lines.append("")
    report_lines.append(f"{'PERIOD SUMMARY':^70}")
    report_lines.append("-"*70)
    report_lines.append(f"Start Date:        {portfolio_value.index[0].strftime('%Y-%m-%d')}")
    report_lines.append(f"End Date:          {portfolio_value.index[-1].strftime('%Y-%m-%d')}")
    report_lines.append(f"Duration:          {days} days ({months:.1f} months / {years:.2f} years)")
    report_lines.append("")
    report_lines.append(f"{'PORTFOLIO VALUES':^70}")
    report_lines.append("-"*70)
    report_lines.append(f"Initial Value:     ${initial:>15,.2f}")
    report_lines.append(f"Final Value:       ${final:>15,.2f}")
    report_lines.append(f"Absolute Change:   ${absolute_change:>15,.2f}")
    report_lines.append(f"Total Return:      {total_return:>15.2f}%")
    report_lines.append("")
    report_lines.append(f"{'S&P 500 BENCHMARK':^70}")
    report_lines.append("-"*70)
    report_lines.append(f"Initial Value:     ${benchmark_initial:>15,.2f}")
    report_lines.append(f"Final Value:       ${benchmark_final:>15,.2f}")
    report_lines.append(f"Absolute Change:   ${benchmark_absolute_change:>15,.2f}")
    report_lines.append(f"Total Return:      {benchmark_total_return:>15.2f}%")
    report_lines.append("")
    report_lines.append(f"{'ANNUALIZED RETURNS':^70}")
    report_lines.append("-"*70)
    report_lines.append(f"Portfolio CAGR:    {cagr:>15.2f}%")
    report_lines.append(f"S&P 500 CAGR:      {benchmark_cagr:>15.2f}%")
    report_lines.append(f"Outperformance:    {(cagr - benchmark_cagr):>15.2f}%")
    report_lines.append("")
    report_lines.append(f"{'PORTFOLIO STATISTICS':^70}")
    report_lines.append("-"*70)
    report_lines.append(f"Peak Value:        ${max_value:>15,.2f}  ({max_date.strftime('%Y-%m-%d')})")
    report_lines.append(f"Lowest Value:      ${min_value:>15,.2f}  ({min_date.strftime('%Y-%m-%d')})")
    report_lines.append(f"Max Drawdown:      {max_drawdown:>15.2f}%")
    
    report_text = "\n".join(report_lines)
    
    # Create summary DataFrame
    summary_data = {
        'Metric': [
            'Initial Portfolio Value', 'Final Portfolio Value', 'Absolute Change', 'Total Return (%)',
            'Initial Benchmark Value', 'Final Benchmark Value', 'Benchmark Absolute Change', 'Benchmark Total Return (%)',
            'Portfolio CAGR (%)', 'Benchmark CAGR (%)', 'Outperformance (%)',
            'Max Drawdown (%)', 'Peak Value', 'Lowest Value'
        ],
        'Value': [
            initial, final, absolute_change, total_return,
            benchmark_initial, benchmark_final, benchmark_absolute_change, benchmark_total_return,
            cagr, benchmark_cagr, cagr - benchmark_cagr,
            max_drawdown, max_value, min_value
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    
    # Create Plotly figures
    figures = {}
    
    # 1. Sector Allocation (Stacked Area Chart)
    fig_sector = go.Figure()
    for col in weights.columns:
        fig_sector.add_trace(go.Scatter(
            x=weights.index,
            y=weights[col],
            name=col,
            stackgroup='one',
            fillcolor=SECTOR_COLORS.get(col, '#808080'),
            mode='lines',
            line=dict(width=0.5, color=SECTOR_COLORS.get(col, '#808080'))
        ))
    fig_sector.update_layout(
        title='Sector Allocation',
        xaxis_title='Date',
        yaxis_title='Weight (%)',
        hovermode='x unified',
        height=600,
        showlegend=True
    )
    figures['sector_allocation'] = fig_sector
    
    # 2. Portfolio Value and Cumulative Returns
    fig_performance = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Portfolio Value', 'Cumulative Returns'),
        vertical_spacing=0.1,
        shared_xaxes=True
    )
    
    # Portfolio Value
    fig_performance.add_trace(
        go.Scatter(x=portfolio_value.index, y=portfolio_value.values, name='SMIC Portfolio',
                  line=dict(color='#1f77b4', width=3)),
        row=1, col=1
    )
    fig_performance.add_trace(
        go.Scatter(x=benchmark_value.index, y=benchmark_value.values, name='S&P 500',
                  line=dict(color='#d62728', width=3, dash='dash')),
        row=1, col=1
    )
    
    # Cumulative Returns
    fig_performance.add_trace(
        go.Scatter(x=portfolio_cumulative_return.index, y=portfolio_cumulative_return.values,
                  name='SMIC Portfolio', line=dict(color='#1f77b4', width=3)),
        row=2, col=1
    )
    fig_performance.add_trace(
        go.Scatter(x=benchmark_cumulative_return.index, y=benchmark_cumulative_return.values,
                  name='S&P 500', line=dict(color='#d62728', width=3, dash='dash')),
        row=2, col=1
    )
    
    fig_performance.update_xaxes(title_text="Date", row=2, col=1)
    fig_performance.update_yaxes(title_text="USD", row=1, col=1)
    fig_performance.update_yaxes(title_text="Return (%)", row=2, col=1)
    fig_performance.update_layout(height=800, showlegend=True, hovermode='x unified')
    figures['performance'] = fig_performance
    
    # 3. ETF vs Stocks (Stacked Area Subplots)
    fig_etf_vs_stocks = make_subplots(
        rows=2, cols=1,
        subplot_titles=('ETF Weights by Sector', 'Individual Stocks Weights by Sector'),
        vertical_spacing=0.1,
        shared_xaxes=True
    )
    
    # Top panel: ETF weights
    etf_cols = [col for col in sector_etf_stocks.columns if col.endswith('_ETF')]
    etf_df = sector_etf_stocks[etf_cols].copy()
    etf_df.columns = [col.replace('_ETF', '') for col in etf_df.columns]
    for col in etf_df.columns:
        fig_etf_vs_stocks.add_trace(go.Scatter(
            x=etf_df.index, y=etf_df[col], name=col,
            stackgroup='one', fillcolor=SECTOR_COLORS.get(col, '#808080'),
            mode='lines', line=dict(width=0.5, color=SECTOR_COLORS.get(col, '#808080'))
        ), row=1, col=1)
    
    # Bottom panel: Individual Stocks weights
    stocks_cols = [col for col in sector_etf_stocks.columns if col.endswith('_Stocks')]
    stocks_df = sector_etf_stocks[stocks_cols].copy()
    stocks_df.columns = [col.replace('_Stocks', '') for col in stocks_df.columns]
    for col in stocks_df.columns:
        fig_etf_vs_stocks.add_trace(go.Scatter(
            x=stocks_df.index, y=stocks_df[col], name=col,
            stackgroup='two', fillcolor=SECTOR_COLORS.get(col, '#808080'),
            mode='lines', line=dict(width=0.5, color=SECTOR_COLORS.get(col, '#808080'))
        ), row=2, col=1)
    
    fig_etf_vs_stocks.update_xaxes(title_text="Date", row=2, col=1)
    fig_etf_vs_stocks.update_yaxes(title_text="Weight (%)", row=1, col=1)
    fig_etf_vs_stocks.update_yaxes(title_text="Weight (%)", row=2, col=1)
    fig_etf_vs_stocks.update_layout(height=800, showlegend=True, hovermode='x unified')
    figures['etf_vs_stocks'] = fig_etf_vs_stocks
    
    # 4. ETF vs Stocks (Grouped Bar Chart)
    sectors = ytd_df['Sector'].tolist()
    etf_ends = ytd_df['ETF_Weight_End (%)'].tolist()
    stocks_ends = ytd_df['Stocks_Weight_End (%)'].tolist()
    
    fig_bar_comparison = go.Figure(data=[
        go.Bar(name='ETF', x=sectors, y=etf_ends, marker_color='#2E86AB'),
        go.Bar(name='Individual Stocks', x=sectors, y=stocks_ends, marker_color='#F18F01')
    ])
    fig_bar_comparison.update_layout(
        title='Sector Allocation: ETF vs Individual Stocks (End of Period)',
        xaxis_title='Sector',
        yaxis_title='Weight (%)',
        barmode='group',
        height=600
    )
    figures['bar_comparison'] = fig_bar_comparison
    
    # 5. Weight Drift Over Time (Line Chart)
    weight_drift = weights.copy()
    for col in weight_drift.columns:
        if col in initial_weights:
            weight_drift[col] = weight_drift[col] - initial_weights[col]
        else:
            weight_drift[col] = 0
    
    fig_weight_drift = go.Figure()
    for col in weight_drift.columns:
        max_drift = abs(weight_drift[col]).max()
        if max_drift > 0.5: # Only plot meaningful drift
            fig_weight_drift.add_trace(go.Scatter(
                x=weight_drift.index,
                y=weight_drift[col],
                name=col,
                mode='lines',
                line=dict(width=2.5, color=SECTOR_COLORS.get(col, '#808080'))
            ))
            
    fig_weight_drift.update_layout(
        title='Sector Weight Drift (Change from Initial Allocation)',
        xaxis_title='Date',
        yaxis_title='Weight Change (%)',
        hovermode='x unified',
        height=600
    )
    figures['weight_drift'] = fig_weight_drift
    
    return report_text, figures, summary_df, ytd_df

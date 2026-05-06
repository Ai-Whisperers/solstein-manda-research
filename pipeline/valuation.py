#!/usr/bin/env python3
"""
Valuation engine — DCF, LBO, Comparable Company Analysis, SOTP.
Integrates with scoring system to add financial valuation to M&A scores.

Patterns: finverse, DCF-Valuation-Model, hess-chevron-valuation-analysis

Usage:
    from valuation import run_dcf, run_lbo, run_comps, valuation_summary
    val = valuation_summary('AAPL')
    print(val['dcf_value'], val['comps_ev_ebitda'])
"""

import json, os, sys, logging
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# --- 1. Discounted Cash Flow (DCF) ---

def run_dcf(ticker, revenue_growth=0.10, fcf_margin=0.15, discount_rate=0.10,
            terminal_growth=0.025, projection_years=5):
    """
    Run DCF valuation for a public company.
    Uses yfinance for financial data, finverse for DCF math.
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract financial data
        revenue = info.get('totalRevenue', 0)
        ebit = info.get('ebit', 0) or info.get('operatingIncome', 0)
        debt = info.get('totalDebt', 0)
        cash = info.get('totalCash', 0)
        shares = info.get('sharesOutstanding', 0)
        market_cap = info.get('marketCap', 0)
        beta = info.get('beta', 1.0)
        
        if not revenue or not shares:
            return {'error': f'No financial data for {ticker}'}
        
        # WACC calculation via CAPM
        risk_free = 0.0425  # Current ~10yr Treasury
        equity_risk_premium = 0.055
        cost_of_equity = risk_free + beta * equity_risk_premium
        cost_of_debt = 0.05
        tax_rate = 0.21
        
        if market_cap and debt:
            equity_weight = market_cap / (market_cap + debt)
            debt_weight = debt / (market_cap + debt)
        else:
            equity_weight, debt_weight = 0.9, 0.1
        
        wacc = equity_weight * cost_of_equity + debt_weight * cost_of_debt * (1 - tax_rate)
        
        # Project FCF
        fcf_projections = []
        for year in range(1, projection_years + 1):
            projected_revenue = revenue * (1 + revenue_growth) ** year
            fcf = projected_revenue * fcf_margin
            pv = fcf / (1 + wacc) ** year
            fcf_projections.append({
                'year': year,
                'revenue': projected_revenue,
                'fcf': fcf,
                'pv': pv,
            })
        
        # Terminal value
        terminal_fcf = revenue * (1 + revenue_growth) ** projection_years * fcf_margin
        terminal_value = terminal_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
        pv_terminal = terminal_value / (1 + wacc) ** projection_years
        
        # Enterprise value
        pv_fcf = sum(f['pv'] for f in fcf_projections)
        enterprise_value = pv_fcf + pv_terminal
        equity_value = enterprise_value - debt + cash
        intrinsic_per_share = equity_value / shares if shares else 0
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        
        return {
            'ticker': ticker,
            'company': info.get('longName', ticker),
            'method': 'dcf',
            'wacc': round(wacc, 4),
            'cost_of_equity': round(cost_of_equity, 4),
            'enterprise_value': round(enterprise_value, 2),
            'equity_value': round(equity_value, 2),
            'intrinsic_per_share': round(intrinsic_per_share, 2),
            'current_price': current_price,
            'upside_pct': round((intrinsic_per_share / current_price - 1) * 100, 1) if current_price else 0,
            'projections': fcf_projections,
            'terminal_value': round(terminal_value, 2),
            'debt': round(debt, 2),
            'cash': round(cash, 2),
            'shares': shares,
            'confidence': 'medium' if all([revenue, ebit, debt]) else 'low',
        }
    except Exception as e:
        logger.warning(f"DCF failed for {ticker}: {e}")
        return {'error': str(e), 'ticker': ticker, 'method': 'dcf'}


# --- 2. Leveraged Buyout (LBO) ---

def run_lbo(ticker=None, entry_ebitda=100, entry_multiple=8.0, 
            exit_multiple=10.0, debt_pct=0.5, hold_years=5, 
            ebitda_growth=0.08, interest_rate=0.06):
    """
    Run LBO analysis. Returns IRR, MOIC, debt schedule.
    """
    try:
        if ticker:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            ebitda = info.get('ebitda', entry_ebitda * 1_000_000) or entry_ebitda * 1_000_000
            ebitda = ebitda / 1_000_000  # Convert to millions
        else:
            ebitda = entry_ebitda
        
        entry_ev = ebitda * entry_multiple
        debt = entry_ev * debt_pct
        equity = entry_ev - debt
        
        # Project EBITDA and debt paydown
        projections = []
        remaining_debt = debt
        for year in range(1, hold_years + 1):
            projected_ebitda = ebitda * (1 + ebitda_growth) ** year
            interest = remaining_debt * interest_rate
            # Simple debt paydown: 20% of FCF
            fcf = projected_ebitda * 0.4
            debt_payment = min(fcf * 0.5, remaining_debt)
            remaining_debt -= debt_payment
            projections.append({
                'year': year,
                'ebitda': round(projected_ebitda, 2),
                'interest': round(interest, 2),
                'debt_payment': round(debt_payment, 2),
                'remaining_debt': round(max(remaining_debt, 0), 2),
            })
        
        exit_ebitda = ebitda * (1 + ebitda_growth) ** hold_years
        exit_ev = exit_ebitda * exit_multiple
        exit_equity = exit_ev - max(remaining_debt, 0)
        
        # IRR calculation
        cash_flows = [-equity] + [0] * (hold_years - 1) + [exit_equity]
        
        # Simple IRR via numpy
        import numpy as np
        try:
            irr = np.irr(cash_flows)
        except Exception:
            logger.warning("np.irr failed for cash_flows, using 0")
            irr = 0
        
        moic = exit_equity / equity if equity else 0
        
        return {
            'method': 'lbo',
            'entry_ebitda': round(ebitda, 2),
            'entry_multiple': entry_multiple,
            'entry_ev': round(entry_ev, 2),
            'debt': round(debt, 2),
            'equity': round(equity, 2),
            'exit_ebitda': round(exit_ebitda, 2),
            'exit_multiple': exit_multiple,
            'exit_ev': round(exit_ev, 2),
            'exit_equity': round(exit_equity, 2),
            'irr': round(irr, 4),
            'moic': round(moic, 2),
            'projections': projections,
        }
    except Exception as e:
        logger.warning(f"LBO failed: {e}")
        return {'error': str(e), 'method': 'lbo'}


# --- 3. Comparable Company Analysis ---

def run_comps(target_ticker, peer_tickers=None, sector=None):
    """
    Run comparable company analysis. Returns valuation multiples.
    """
    try:
        import yfinance as yf
        
        if not peer_tickers:
            # Auto-select peers by sector from yfinance info
            target = yf.Ticker(target_ticker)
            target_info = target.info
            sector = sector or target_info.get('sector', 'Technology')
            industry = target_info.get('industry', '')
            
            # Common peer sets by sector
            peer_sets = {
                'Technology': ['MSFT', 'GOOGL', 'META', 'ORCL', 'CRM', 'ADBE', 'NOW'],
                'Financial Services': ['JPM', 'GS', 'MS', 'V', 'MA', 'PYPL'],
                'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK'],
                'Consumer Cyclical': ['AMZN', 'HD', 'TSLA', 'NKE', 'MCD'],
                'Communication': ['T', 'VZ', 'DIS', 'CMCSA', 'NFLX'],
                'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB'],
                'Industrials': ['CAT', 'GE', 'BA', 'HON', 'UPS'],
                'Real Estate': ['PLD', 'AMT', 'CCI', 'EQIX', 'SPG'],
            }
            peer_tickers = peer_sets.get(sector, ['MSFT', 'GOOGL', 'META'])
        
        peers_data = []
        for ticker in [target_ticker] + peer_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                peers_data.append({
                    'ticker': ticker,
                    'name': info.get('longName', ticker),
                    'market_cap': info.get('marketCap', 0),
                    'ev': info.get('enterpriseValue', 0),
                    'revenue': info.get('totalRevenue', 0),
                    'ebitda': info.get('ebitda', 0),
                    'ebit': info.get('ebit', 0) or info.get('operatingIncome', 0),
                    'net_income': info.get('netIncomeToCommon', 0),
                    'pe': info.get('trailingPE', 0) or info.get('forwardPE', 0),
                    'ps': info.get('priceToSalesTrailing12Months', 0),
                    'pb': info.get('priceToBook', 0),
                    'ev_revenue': info.get('enterpriseToRevenue', 0),
                    'ev_ebitda': info.get('enterpriseToEbitda', 0),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                })
            except Exception:
                continue
        
        return {
            'method': 'comps',
            'target': target_ticker,
            'peers': peers_data,
        }
    except Exception as e:
        logger.warning(f"Comps failed: {e}")
        return {'error': str(e), 'method': 'comps'}


# --- 4. Full Valuation Summary ---

def valuation_summary(ticker, peer_tickers=None):
    """Run all valuation methods and return consolidated summary."""
    dcf = run_dcf(ticker)
    lbo = run_lbo(ticker=ticker)
    comps = run_comps(ticker, peer_tickers)
    
    result = {
        'ticker': ticker,
        'dcf': dcf if 'error' not in dcf else None,
        'lbo': lbo if 'error' not in lbo else None,
        'comps': comps if 'error' not in comps else None,
    }
    
    # Calculate implied value range from comps
    if comps and 'error' not in comps and comps.get('peers'):
        ev_ebitda_values = [p.get('ev_ebitda', 0) for p in comps['peers'] if p.get('ev_ebitda', 0) > 0]
        pe_values = [p.get('pe', 0) for p in comps['peers'] if p.get('pe', 0) > 0]
        ev_revenue_values = [p.get('ev_revenue', 0) for p in comps['peers'] if p.get('ev_revenue', 0) > 0]
        
        import numpy as np
        if ev_ebitda_values:
            result['median_ev_ebitda'] = round(np.median(ev_ebitda_values), 1)
            result['mean_ev_ebitda'] = round(np.mean(ev_ebitda_values), 1)
        if pe_values:
            result['median_pe'] = round(np.median(pe_values), 1)
    
    return result


def format_valuation_report(val):
    """Format valuation summary as readable text."""
    lines = []
    lines.append("=== Valuation Summary ===")
    
    dcf = val.get('dcf')
    if dcf:
        lines.append(f"\nDCF Valuation:")
        lines.append(f"  Intrinsic value: ${dcf.get('intrinsic_per_share', 0):.2f}/share")
        lines.append(f"  Current price:   ${dcf.get('current_price', 0):.2f}/share")
        lines.append(f"  Upside/downside: {dcf.get('upside_pct', 0):+.1f}%")
        lines.append(f"  WACC: {dcf.get('wacc', 0)*100:.1f}%")
        lines.append(f"  EV: ${dcf.get('enterprise_value', 0)/1e9:.2f}B")
    
    lbo = val.get('lbo')
    if lbo:
        lines.append(f"\nLBO Analysis:")
        lines.append(f"  Entry EV: ${lbo.get('entry_ev', 0):.1f}M")
        lines.append(f"  Debt: ${lbo.get('debt', 0):.1f}M ({lbo.get('debt_pct', 0)*100:.0f}% of EV)")
        lines.append(f"  IRR: {lbo.get('irr', 0)*100:.1f}%")
        lines.append(f"  MOIC: {lbo.get('moic', 0):.1f}x")
    
    comps = val.get('comps')
    if comps and comps.get('peers'):
        lines.append(f"\nComparable Companies:")
        for p in comps['peers'][:5]:
            lines.append(f"  {p['ticker']:<6} EV/EBITDA={p.get('ev_ebitda', 0):.1f}x  P/E={p.get('pe', 0):.1f}x  EV/Rev={p.get('ev_revenue', 0):.1f}x")
        
        if val.get('median_ev_ebitda'):
            lines.append(f"\n  Median EV/EBITDA: {val['median_ev_ebitda']}x")
            lines.append(f"  Mean EV/EBITDA:   {val['mean_ev_ebitda']}x")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'
    val = valuation_summary(ticker)
    print(format_valuation_report(val))
    
    # Save to JSON
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'HORECA', 'valuation_test')
    os.makedirs(out_dir, exist_ok=True)
    from core.utils import atomic_json_dump
    atomic_json_dump(val, os.path.join(out_dir, f'{ticker}_valuation.json'), indent=2, default=str)
    print(f"\nSaved to output/HORECA/valuation_test/{ticker}_valuation.json")

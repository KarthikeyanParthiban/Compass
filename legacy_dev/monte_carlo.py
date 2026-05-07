import os
import json
import hashlib
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta

from dotenv import load_dotenv

load_dotenv()
np.random.seed(42)



# from Main import get_groww_holdings, ACCESS_TOKEN # REMOVED FOR PRIVACY

# ── Disk-cache config ──────────────────────────────────────────────────────
BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR          = os.path.join(BASE_DIR, "price_cache")
SIM_CACHE_DIR      = os.path.join(BASE_DIR, "sim_cache")
HOLDINGS_CACHE     = os.path.join(CACHE_DIR, 'groww_holdings.json')
CACHE_TTL_HOURS    = 24          # re-download once per day
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(SIM_CACHE_DIR, exist_ok=True)


def _cache_key(*args):
    """Generate a unique key for the inputs."""
    s = "|".join(map(str, args))
    return hashlib.md5(s.encode()).hexdigest()


def _is_fresh(path: str, ttl_hours: int = CACHE_TTL_HOURS) -> bool:
    """True if file exists and was modified within TTL."""
    if not os.path.exists(path):
        return False
    age_hours = (datetime.now(timezone.utc).timestamp() - os.path.getmtime(path)) / 3600
    return age_hours < ttl_hours


# Management Strategy Profiles (Average Investor Personas)
STRATEGY_PROFILES = {
    'sample':          {'name': 'Sample Growth Portfolio', 'user_name': 'Investor', 'symbols': ['RELIANCE.NS','TCS.NS','HDFCBANK.NS','INFY.NS'], 'quantities': [10, 5, 20, 15]},
    'index_follower':  {'name': 'Passive Index Follower',  'user_name': 'Siddharth','symbols': ['NIFTYBEES.NS','JUNIORBEES.NS','HDFCGOLD.NS'], 'quantities': [500,200,300]},
    'growth_retail':   {'name': 'Growth-Focused Retail',   'user_name': 'Priyanka', 'symbols': ['RELIANCE.NS','TATAELXSI.NS','TITAN.NS','TATASTEEL.NS'], 'quantities': [50,20,30,200]},
    'dividend_king':   {'name': 'Dividend Income Seeker',  'user_name': 'Vikram',   'symbols': ['ITC.NS','SBIN.NS','HDFCBANK.NS','COALINDIA.NS'], 'quantities': [200,100,50,300]},
    'tech_visionary':  {'name': 'High-Growth Tech Vision', 'user_name': 'Ishita',   'symbols': ['ITBEES.NS','MON100.NS','TCS.NS','INFY.NS'], 'quantities': [1000,200,20,50]},
    'balanced_hybrid': {'name': 'Balanced Hybrid (Safe)',  'user_name': 'Rajesh',   'symbols': ['NIFTYBEES.NS','BANKBEES.NS','SILVERBEES.NS','HDFCGOLD.NS'], 'quantities': [400,200,500,500]},
}


def load_portfolio_data():
    """Returns a static sample portfolio for public demo."""
    profile = STRATEGY_PROFILES['sample']
    return profile['symbols'], profile['quantities']


def fetch_prices_groww(symbols, period='5y'):
    """Disabled for public privacy. Use fetch_historical_prices for yfinance fallback."""
    return None


def fetch_historical_prices(symbols, quantities, period='5y'):
    """
    Load prices from Parquet on disk.
    Tries Groww API first, falls back to Yahoo Finance.
    """
    if not symbols:
        print("[warn] No symbols provided to fetch_historical_prices.")
        return pd.DataFrame(), []

    key      = _cache_key(",".join(sorted(symbols)), period)
    parquet  = os.path.join(CACHE_DIR, f"{key}.parquet")
    meta     = os.path.join(CACHE_DIR, f"{key}.symbols.json")

    if _is_fresh(parquet):
        print(f"[cache] Loading prices from disk ({parquet}).")
        raw = pd.read_parquet(parquet)
    else:
        # 1. Try Groww First
        raw = fetch_prices_groww(symbols, period)
        
        if raw is None or raw.empty:
            print(f"[api]   Groww unavailable/expired. Falling back to yfinance...")
            df = yf.download(symbols, period=period, progress=False)
            if df.empty:
                print(f"[error] Yahoo Finance returned no data for symbols: {symbols}")
                raw = pd.DataFrame(columns=symbols)
            else:
                if isinstance(df.columns, pd.MultiIndex):
                    # Handle YFinance multi-index (Price, Symbol)
                    lvl0 = df.columns.get_level_values(0)
                    if 'Adj Close' in lvl0: raw = df['Adj Close']
                    elif 'Close' in lvl0: raw = df['Close']
                    else: raw = df[lvl0[0]]
                else:
                    raw = df

        # Ensure raw has columns for all symbols, filling missing with NaN
        for s in symbols:
            if s not in raw.columns:
                raw[s] = np.nan

        raw = raw.ffill().dropna(axis=1, how='all')
        raw.to_parquet(parquet)
        # Save symbol list so we can map back to quantities
        with open(meta, 'w') as f:
            json.dump(raw.columns.tolist(), f)
        print(f"[cache] Saved prices to {parquet} ({len(raw)} rows, {len(raw.columns)} symbols).")

    # Map quantities to the columns actually present in the final data
    saved_syms = raw.columns.tolist()
    sym_to_qty = dict(zip(symbols, quantities))
    final_qtys = [sym_to_qty.get(s, 0) for s in saved_syms]
    
    print(f"[debug] Final symbols: {saved_syms}")
    print(f"[debug] Final quantities: {final_qtys}")
    
    return raw, final_qtys


class PortfolioEngine:
    def __init__(self, prices, quantities, num_sims=1000, days=252):
        self.prices       = prices
        self.quantities   = np.array(quantities)
        self.num_sims     = num_sims
        self.days         = days
        self.returns      = prices.ffill().pct_change().fillna(0)
        self.current_prices = prices.ffill().iloc[-1].values
        self.current_value  = float(np.sum(self.current_prices * self.quantities))
        self.weights        = (self.current_prices * self.quantities) / self.current_value

    def _cholesky(self, cov):
        try:
            return np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            return np.linalg.cholesky(cov + np.eye(len(cov)) * 1e-8)

    def _run_mc(self, mean_ret, cov, start_val, days, n_sims):
        L   = self._cholesky(cov)
        out = np.zeros((days, n_sims))
        df  = 5
        sc  = np.sqrt((df - 2) / df)
        for i in range(n_sims):
            z      = np.random.standard_t(df, size=(days, len(self.weights))) * sc
            dr     = mean_ret.values + np.dot(z, L.T)
            pg     = np.dot(dr, self.weights)
            out[:, i] = start_val * np.cumprod(1 + pg)
        return out

    def run_monte_carlo(self):
        return self._run_mc(
            self.returns.mean(), self.returns.cov(),
            self.current_value, self.days, self.num_sims
        )

    def run_validation(self):
        """Walk-forward: train on everything before last 252 days, validate on last 252."""
        split = -252
        train = self.prices.iloc[:split].pct_change().dropna()
        val   = self.prices.iloc[split:]

        start_val = float(np.sum(val.iloc[0].values * self.quantities))
        paths     = self._run_mc(train.mean(), train.cov(), start_val, len(val), 500)
        actual    = (val / val.iloc[0]).values @ self.weights * start_val

        return {
            'sim_mean':  np.mean(paths, axis=1).tolist(),
            'sim_upper': np.percentile(paths, 95, axis=1).tolist(),
            'sim_lower': np.percentile(paths, 5,  axis=1).tolist(),
            'actual':    actual.tolist(),
            'dates':     val.index.strftime('%Y-%m-%d').tolist(),
        }

    def run_backtest(self):
        # Fill NaNs with 1.0 (no growth) for the index calc to avoid NaN results
        p_filled = self.prices.ffill().bfill()
        growth = (p_filled / p_filled.iloc[0]).values @ self.weights
        return (growth * self.current_value).tolist(), \
               self.prices.index.strftime('%Y-%m-%d').tolist()


def _monthly_bars(paths, current_value, horizon_years):
    """
    Sample paths at monthly intervals (~21 trading days).
    Returns a list of dicts: {label, median, p15, p85, p5, p95}
    ready for a bar chart.
    """
    days_total   = paths.shape[0]
    trading_per_month = 21
    
    bars = [{
        'label': 'Now',
        'milestone': 'Now',
        'is_milestone': True,
        'month': 0,
        'median': float(current_value),
        'p15':    float(current_value),
        'p85':    float(current_value),
        'p5':     float(current_value),
        'p95':    float(current_value),
        'above':  True
    }]
    
    milestones = {12: '12M', 24: '24M', 36: '36M', 48: '48M', 60: '60M'}
    month_idx = 0
    d = trading_per_month  # start at end of month 1
    while d <= days_total:
        month_idx += 1
        vals   = paths[d - 1, :]
        
        milestone = milestones.get(month_idx)

        bars.append({
            'label':  f"Month {month_idx}",
            'milestone': milestone,
            'is_milestone': milestone is not None,
            'month': month_idx,
            'median': float(np.percentile(vals, 50)),
            'p15':    float(np.percentile(vals, 15)),
            'p85':    float(np.percentile(vals, 85)),
            'p5':     float(np.percentile(vals,  5)),
            'p95':    float(np.percentile(vals, 95)),
            'above':  bool(np.percentile(vals, 50) >= current_value),
        })
        d += trading_per_month

    # ── Smoothing: Eliminate monthly 'jitter' for a premium look ──
    df_bars = pd.DataFrame(bars)
    cols_to_smooth = ['median', 'p15', 'p85', 'p5', 'p95']
    for col in cols_to_smooth:
        df_bars[col] = df_bars[col].rolling(window=3, min_periods=1, center=True).mean()
    
    # Year 0 must stay exactly at current_value
    for col in cols_to_smooth:
        df_bars.loc[0, col] = current_value

    return df_bars.replace({np.nan: None}).to_dict('records')


def get_management_data(profile_id='current', num_sims=1000, days=1260, confidence_level=95):
    # 1. Select profile
    profile = STRATEGY_PROFILES.get(profile_id, STRATEGY_PROFILES['sample'])
    if profile_id == 'sample':
        symbols, quantities = load_portfolio_data()
    else:
        symbols, quantities = profile['symbols'], profile['quantities']

    # 2. Generate Fast Cache Key (based on date, profile, and params)
    sim_key = _cache_key(profile_id, days, num_sims, date.today())
    sim_cache_path = os.path.join(SIM_CACHE_DIR, f"sim_{sim_key}.json")

    if os.path.exists(sim_cache_path):
        print(f"[cache] -> INSTANT HIT: Simulation results for {profile_id}")
        with open(sim_cache_path, 'r') as f:
            return json.load(f)

    # 3. Fetch prices (if cache miss)
    prices, final_qtys = fetch_historical_prices(symbols, quantities)

    # 3. Build engine & run
    engine = PortfolioEngine(prices, final_qtys, num_sims=num_sims, days=days)
    paths  = engine.run_monte_carlo()

    # 4. Backtest & validation
    backtest_values, backtest_dates = engine.run_backtest()
    validation = engine.run_validation()

    # 5. Metrics
    final_vals = paths[-1, :]
    var_val    = float(np.percentile(final_vals, 100 - confidence_level))
    actuals = np.array(validation['actual'])
    within  = np.logical_and(actuals >= np.array(validation['sim_lower']),
                              actuals <= np.array(validation['sim_upper']))
    reliability = float(np.mean(within) * 100)

    years = days / 252
    def calc_cagr(val):
        if engine.current_value <= 0: return 0.0
        return float(((val / engine.current_value) ** (1 / years) - 1) * 100)

    outcomes = {
        'pessimistic': float(np.percentile(final_vals, 15)),
        'conservative':float(np.percentile(final_vals, 25)),
        'expected':    float(np.percentile(final_vals, 50)),
        'growth':      float(np.percentile(final_vals, 75)),
        'optimistic':  float(np.percentile(final_vals, 85)),
    }
    cagrs = {k: calc_cagr(v) for k, v in outcomes.items()}

    # 6. Calculate historical stock-level Performance (1Y Absolute, 3Y/5Y CAGR)
    # We calculate per-stock to avoid truncation from newer symbols
    stock_stats = []
    for sym in prices.columns:
        s_data = prices[sym].dropna()
        n = len(s_data)
        
        # 1Y Absolute
        ret_1y = float((s_data.iloc[-1] / s_data.iloc[-252] - 1) * 100) if n >= 252 else 0.0
        # 3Y/5Y CAGR: ((PriceNow / PriceThen) ^ (1/Years) - 1) * 100
        cagr_3y = float(((s_data.iloc[-1] / s_data.iloc[-756]) ** (1/3) - 1) * 100) if n >= 756 else 0.0
        cagr_5y = float(((s_data.iloc[-1] / s_data.iloc[0]) ** (1/5) - 1) * 100) if n >= 1260 else 0.0
        
        stock_stats.append({
            'symbol': sym,
            'weight': float(engine.weights[prices.columns.get_loc(sym)] * 100),
            'ret_1y': ret_1y,
            'cagr_3y': cagr_3y,
            'cagr_5y': cagr_5y,
        })
    monthly = _monthly_bars(paths, engine.current_value, days // 252)

    result = {
        'profile_id':       profile_id,
        'profile_name':     profile['name'],
        'current_value':    engine.current_value,
        'mean_end':         float(np.mean(final_vals)),
        'outcomes':         outcomes,
        'cagrs':            cagrs,
        'var_value':        var_val,
        'prob_profit':      float((final_vals > engine.current_value).mean()),
        'reliability_score':reliability,
        'holdings':         stock_stats,
        'weights':          {s: float(w) for s, w in zip(prices.columns, engine.weights)},
        'monthly_bars':     monthly,
        'backtest_data':    backtest_values,
        'backtest_dates':   backtest_dates,
        'validation':       validation,
        'metadata': {
            'user_name':    profile['user_name'],
            'profile_name': profile['name'],
            'prob_profit':  float((final_vals > engine.current_value).mean())
        }
    }

    # Save to disk
    if engine.current_value > 0:
        with open(sim_cache_path, 'w') as f:
            json.dump(result, f)
    else:
        print(f"[warn] Simulation produced zero value for {profile_id}. Not caching.")
        
    return result


def get_available_profiles():
    return [{'id': k, 'name': v['name']} for k, v in STRATEGY_PROFILES.items()]





if __name__ == "__main__":
    result = get_management_data('current', num_sims=500, days=252)
    print(f"Current: ₹{result['current_value']:,.0f}")
    print(f"Expected 1Y: ₹{result['outcomes']['expected']:,.0f}")

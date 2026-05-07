"""
SageMaker Inference Handler for Monte Carlo Portfolio Simulation.
"""

import os
import json
import logging
import io

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

np.random.seed(42)

# ── Global Constants ─────────────────────────────────────────────────────────
TRADING_DAYS_PER_MONTH = 21
TRADING_DAYS_PER_YEAR = 252
PROJECTION_MONTHS = 60          # 5-year horizon
PROJECTION_DAYS = PROJECTION_MONTHS * TRADING_DAYS_PER_MONTH  # 1260 trading days
DEFAULT_NUM_SIMS = 5000
STUDENT_T_DF = 5                # degrees of freedom for fat tails
HISTORICAL_PERIOD = "2y"        # 2Y lookback for speed and correlation stability

# ── Cache directory ──────────────────────────────────────────────────────────
CACHE_DIR = "/tmp/price_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class MonteCarloEngine:
    def __init__(self, prices: pd.DataFrame, quantities: np.ndarray,
                 num_sims: int = DEFAULT_NUM_SIMS, days: int = PROJECTION_DAYS):
        self.prices = prices.ffill()
        self.quantities = np.array(quantities, dtype=float)
        self.num_sims = num_sims
        self.days = days

        self.returns = self.prices.pct_change().fillna(0)
        self.current_prices = self.prices.iloc[-1].values
        self.current_value = float(np.sum(self.current_prices * self.quantities))

        if self.current_value > 0:
            self.weights = (self.current_prices * self.quantities) / self.current_value
        else:
            n = len(self.quantities)
            self.weights = np.ones(n) / n

    def _cholesky(self, cov: np.ndarray) -> np.ndarray:
        try:
            return np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            return np.linalg.cholesky(cov + np.eye(len(cov)) * 1e-8)

    def run(self) -> np.ndarray:
        mean_ret = self.returns.mean().values
        cov = self.returns.cov().values
        L = self._cholesky(cov)
        
        scale = np.sqrt((STUDENT_T_DF - 2) / STUDENT_T_DF)
        n_assets = len(self.weights)
        out = np.zeros((self.days, self.num_sims))
        
        batch_size = 500
        for b in range(0, self.num_sims, batch_size):
            current_batch = min(batch_size, self.num_sims - b)
            z = np.random.standard_t(STUDENT_T_DF, size=(current_batch, self.days, n_assets)) * scale
            correlated_z = np.matmul(z, L.T)
            daily_returns = mean_ret + correlated_z
            port_daily_rets = np.matmul(daily_returns, self.weights)
            path_growth = np.cumprod(1 + port_daily_rets, axis=1)
            out[:, b:b+current_batch] = (self.current_value * path_growth).T
            
        return out

def fetch_prices(symbols: list, period: str = HISTORICAL_PERIOD) -> pd.DataFrame:
    logger.info(f"Fetching prices for {len(symbols)} symbols: {symbols[:5]}... Period: {period}")
    
    # Batch download
    df = yf.download(symbols, period=period, progress=False, group_by='column')
    
    if df.empty:
        logger.error("YFinance returned an empty DataFrame.")
        raise ValueError(f"No price data found for the provided symbols.")

    # Robust MultiIndex handling
    if isinstance(df.columns, pd.MultiIndex):
        # We prefer 'Adj Close', then 'Close'
        if 'Adj Close' in df.columns.levels[0]:
            raw = df['Adj Close']
        elif 'Close' in df.columns.levels[0]:
            raw = df['Close']
        else:
            # Fallback to the first available level
            raw = df[df.columns.levels[0][0]]
    else:
        raw = df

    # Final cleanup: Ensure at least some columns survived
    raw = raw.ffill().dropna(axis=1, how="all")
    
    if raw.empty or len(raw.columns) == 0:
        logger.error(f"Dataframe empty after cleanup. Symbols requested: {symbols}")
        raise ValueError("Price data was retrieved but was entirely empty after processing.")

    logger.info(f"Successfully resolved {len(raw.columns)} out of {len(symbols)} symbols.")
    return raw

def build_projections(paths: np.ndarray, current_value: float) -> dict:
    total_days = paths.shape[0]
    final_vals = paths[-1, :]
    
    scenarios = {}
    scenario_defs = {
        "pessimistic": {"percentile": 15, "label": "Bear Case"},
        "expected":    {"percentile": 50, "label": "Base Case"},
        "optimistic":  {"percentile": 85, "label": "Bull Case"},
    }

    for key, cfg in scenario_defs.items():
        pct = cfg["percentile"]
        daily_pcts = np.percentile(paths, pct, axis=1)
        
        monthly_raw = [float(current_value)]
        d = TRADING_DAYS_PER_MONTH
        while d <= total_days:
            monthly_raw.append(float(daily_pcts[d-1]))
            d += TRADING_DAYS_PER_MONTH
        
        if len(monthly_raw) > 3:
            smoothed = []
            for i in range(len(monthly_raw)):
                start = max(0, i - 1)
                end = min(len(monthly_raw), i + 2)
                window = monthly_raw[start:end]
                smoothed.append(sum(window) / len(window))
            smoothed[0] = float(current_value)
            smoothed[-1] = monthly_raw[-1]
            monthly_values = smoothed
        else:
            monthly_values = monthly_raw

        terminal_val = monthly_raw[-1]
        years = PROJECTION_MONTHS / 12
        cagr = ((terminal_val / current_value) ** (1 / years) - 1) * 100 if current_value > 0 else 0
        
        band_lower = float(np.percentile(final_vals, max(pct - 15, 1)))
        band_upper = float(np.percentile(final_vals, min(pct + 15, 99)))

        scenarios[key] = {
            "label": cfg["label"],
            "percentile": pct,
            "monthly_values": [round(v, 2) for v in monthly_values],
            "terminal_value": round(terminal_val, 2),
            "cagr_pct": round(cagr, 2),
            "confidence_band": {
                "lower": round(band_lower, 2),
                "upper": round(band_upper, 2),
            }
        }
    return scenarios

def build_probability_scores(paths: np.ndarray, current_value: float) -> dict:
    final_vals = paths[-1, :]
    prob_profit = float((final_vals > current_value).mean())
    prob_double = float((final_vals > current_value * 2).mean())
    prob_major_loss = float((final_vals < current_value * 0.8).mean())
    var_5 = float(np.percentile(final_vals, 5))
    var_drawdown_pct = round((1 - var_5 / current_value) * 100, 2) if current_value > 0 else 0.0

    return {
        "probability_of_profit": round(prob_profit * 100, 2),
        "probability_of_doubling": round(prob_double * 100, 2),
        "probability_of_major_loss_20pct": round(prob_major_loss * 100, 2),
        "value_at_risk_5pct": round(var_5, 2),
        "var_drawdown_pct": var_drawdown_pct,
        "simulation_count": int(paths.shape[1]),
    }

def model_fn(model_dir):
    return {"engine": "MonteCarloSimulator", "version": "2.1.0"}

def input_fn(request_body, request_content_type="application/json"):
    if request_content_type != "application/json":
        raise ValueError("Unsupported content type. Use application/json.")
    return json.loads(request_body)

def predict_fn(input_data, model):
    holdings = input_data["holdings"]
    num_sims = input_data.get("num_sims", DEFAULT_NUM_SIMS)
    
    symbols = [h["symbol"] for h in holdings]
    quantities = np.array([h["quantity"] for h in holdings], dtype=float)

    prices = fetch_prices(symbols, period=HISTORICAL_PERIOD)
    
    sym_to_qty = dict(zip(symbols, quantities))
    final_symbols = prices.columns.tolist()
    final_quantities = np.array([sym_to_qty.get(s, 0) for s in final_symbols])

    engine = MonteCarloEngine(prices, final_quantities, num_sims=num_sims)
    paths = engine.run()

    result = {
        "portfolio_id": input_data.get("portfolio_id", "custom"),
        "current_value": round(engine.current_value, 2),
        "scenarios": build_projections(paths, engine.current_value),
        "probability_scores": build_probability_scores(paths, engine.current_value),
        "metadata": {
            "engine_version": model["version"],
            "lookback": HISTORICAL_PERIOD,
            "symbols": final_symbols
        }
    }
    return result

def output_fn(prediction, accept="application/json"):
    return json.dumps(prediction, default=str)

if __name__ == "__main__":
    # Local Test
    test_payload = json.dumps({"holdings": [{"symbol": "RELIANCE.NS", "quantity": 10, "value": 25000}]})
    m = model_fn(".")
    d = input_fn(test_payload)
    print(json.dumps(predict_fn(d, m), indent=2))

import os
import json
import logging
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

# Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- CONFIG & CONSTANTS ---
TRADING_DAYS_PER_MONTH = 21
PROJECTION_MONTHS = 60
PROJECTION_DAYS = PROJECTION_MONTHS * TRADING_DAYS_PER_MONTH
DEFAULT_NUM_SIMS = 2000 
STUDENT_T_DF = 5
HISTORICAL_PERIOD = "2y"

# --- CORE MATH ENGINE ---
class MonteCarloEngine:
    def __init__(self, prices: pd.DataFrame, quantities: np.ndarray, num_sims: int, days: int):
        self.prices = prices.ffill().bfill()
        if self.prices.empty:
            raise ValueError("No historical price data available for simulation.")
            
        self.quantities = np.array(quantities, dtype=float)
        self.num_sims = num_sims
        self.days = days
        
        # Calculate returns and handle potential NaNs from flat data
        self.returns = self.prices.pct_change().fillna(0)
        self.current_prices = self.prices.iloc[-1].values
        self.current_value = float(np.sum(self.current_prices * self.quantities))
        
        if self.current_value <= 0:
            raise ValueError(f"Portfolio current value is zero or negative: {self.current_value}")
            
        self.weights = (self.current_prices * self.quantities) / self.current_value

    def run(self):
        mean_ret = self.returns.mean().values
        cov = self.returns.cov().values
        
        # Ensure covariance matrix is positive semi-definite
        try:
            L = np.linalg.cholesky(cov)
        except:
            # Add jitter if Cholesky fails
            L = np.linalg.cholesky(cov + np.eye(len(cov)) * 1e-6)
            
        scale = np.sqrt((STUDENT_T_DF - 2) / STUDENT_T_DF)
        n_assets = len(self.weights)
        out = np.zeros((self.days, self.num_sims))
        
        batch_size = 500
        for b in range(0, self.num_sims, batch_size):
            cur = min(batch_size, self.num_sims - b)
            z = np.random.standard_t(STUDENT_T_DF, size=(cur, self.days, n_assets)) * scale
            correlated_z = np.matmul(z, L.T)
            daily_returns = mean_ret + correlated_z
            port_daily_rets = np.matmul(daily_returns, self.weights)
            path_growth = np.cumprod(1 + port_daily_rets, axis=1)
            out[:, b:b+cur] = (self.current_value * path_growth).T
        return out

# --- UTILS ---
def fetch_prices(symbols):
    logger.info(f"Downloading prices for: {symbols}")
    
    # Try multiple periods if one fails
    for period in [HISTORICAL_PERIOD, "1y", "6mo"]:
        try:
            df = yf.download(
                symbols, 
                period=period, 
                progress=False, 
                group_by='column',
                auto_adjust=True,
                threads=False # More stable in Lambda
            )
            
            if df.empty:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                # Prefer Close over anything else
                if 'Close' in df.columns.levels[0]: raw = df['Close']
                else: raw = df[df.columns.levels[0][0]]
            else:
                raw = df
                
            raw = raw.ffill().dropna(axis=1, how="all")
            
            if not raw.empty and len(raw.columns) > 0:
                logger.info(f"Successfully fetched {len(raw.columns)} symbols using period {period}")
                return raw
        except Exception as e:
            logger.warning(f"Failed to fetch with period {period}: {str(e)}")
            continue
            
    raise ValueError(f"Failed to fetch market data for symbols: {symbols}. Verify ticker names (e.g. RELIANCE.NS)")

def build_projections(paths, current_value):
    total_days = paths.shape[0]
    scenarios = {}
    defs = {"pessimistic": 15, "expected": 50, "optimistic": 85}
    
    for key, pct in defs.items():
        daily_pcts = np.percentile(paths, pct, axis=1)
        monthly_raw = [float(current_value)]
        for d in range(TRADING_DAYS_PER_MONTH, total_days + 1, TRADING_DAYS_PER_MONTH):
            monthly_raw.append(float(daily_pcts[d-1]))
            
        smoothed = []
        for i in range(len(monthly_raw)):
            window = monthly_raw[max(0, i-1):min(len(monthly_raw), i+2)]
            smoothed.append(sum(window)/len(window))
        smoothed[0], smoothed[-1] = monthly_raw[0], monthly_raw[-1]
        
        terminal = monthly_raw[-1]
        cagr = ((terminal/current_value)**(12/PROJECTION_MONTHS)-1)*100 if current_value>0 else 0
        
        scenarios[key] = {
            "label": key.capitalize(),
            "monthly_values": [round(v, 2) for v in smoothed],
            "terminal_value": round(terminal, 2),
            "cagr_pct": round(cagr, 2)
        }
    return scenarios

# --- LAMBDA HANDLER ---
def handler(event, context):
    method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    if method == 'OPTIONS':
        return _resp(200, {"message": "OK"})

    try:
        body_str = event.get('body', '{}')
        if event.get('isBase64Encoded'):
            import base64
            body_str = base64.b64decode(body_str).decode('utf-8')
        
        body = json.loads(body_str)
        holdings = body.get('holdings', [])
        num_sims = body.get('num_sims', DEFAULT_NUM_SIMS)
        
        if not holdings:
            return _resp(400, {"error": "No holdings provided"})

        symbols = [h['symbol'] for h in holdings]
        quantities = [h['quantity'] for h in holdings]
        
        # 1. Fetch Prices
        prices = fetch_prices(symbols)
        
        # 2. Match quantities to available prices
        sym_to_qty = dict(zip(symbols, quantities))
        final_symbols = prices.columns.tolist()
        final_qtys = [sym_to_qty.get(s, 0) for s in final_symbols]
        
        # 3. Simulation
        engine = MonteCarloEngine(prices, final_qtys, num_sims, PROJECTION_DAYS)
        paths = engine.run()
        
        # 4. Metrics
        final_values = paths[-1, :]
        prob_profit = (final_values > engine.current_value).mean()
        prob_double = (final_values > (engine.current_value * 2)).mean()
        
        returns_at_end = (final_values / engine.current_value) - 1
        var_drawdown = np.percentile(returns_at_end, 5)
        
        result = {
            "portfolio_id": body.get("portfolio_id", "unknown"),
            "current_value": round(engine.current_value, 2),
            "scenarios": build_projections(paths, engine.current_value),
            "probability_scores": {
                "probability_of_profit": round(float(prob_profit)*100, 2),
                "probability_of_doubling": round(float(prob_double)*100, 2),
                "var_drawdown_pct": round(abs(float(var_drawdown))*100, 2),
                "simulation_count": num_sims
            }
        }
        return _resp(200, result)

    except Exception as e:
        logger.error(f"Critical Error: {str(e)}")
        # Check for specific Nan issues in Var
        return _resp(400, {"error": str(e)})

def _resp(status, body):
    # Ensure NaN or Infinity doesn't break JSON serialization
    def _clean(obj):
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)): return 0.0
        if isinstance(obj, dict): return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list): return [_clean(v) for v in obj]
        return obj

    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,x-api-key"
        },
        "body": json.dumps(_clean(body))
    }

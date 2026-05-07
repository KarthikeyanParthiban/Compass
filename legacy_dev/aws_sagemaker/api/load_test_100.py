import requests
import json
import time
from datetime import datetime

# API Config
API_URL = "https://35w41kobie.execute-api.ap-south-1.amazonaws.com/default/Compass-MonteCarlo-Bridge"
API_KEY = "wwNacOkQ0o6jTocgeCDtAayvSFANpn9M5ZTU8qDy"

# List of ~100 common Nifty stocks
SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "BHARTIARTL.NS", "SBIN.NS", "ITC.NS", "LT.NS", "HINDUNILVR.NS",
    "AXISBANK.NS", "ADANIENT.NS", "KOTAKBANK.NS", "SUNPHARMA.NS", "M&M.NS", "ULTRACEMCO.NS", "NTPC.NS", "TITAN.NS", "ASIANPAINT.NS", "BAJFINANCE.NS",
    "ADANIPORTS.NS", "MARUTI.NS", "HCLTECH.NS", "COALINDIA.NS", "TATASTEEL.NS", "POWERGRID.NS", "BAJAJFINSV.NS", "INDUSINDBK.NS", "NESTLEIND.NS", "GRASIM.NS",
    "JSWSTEEL.NS", "TECHM.NS", "HINDALCO.NS", "ADANIPOWER.NS", "TATARELI.NS", "SBILIFE.NS", "BPCL.NS", "HDFCLIFE.NS", "DRREDDY.NS", "CIPLA.NS",
    "TATAMOTORS.NS", "BRITANNIA.NS", "WIPRO.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "APOLLOHOSP.NS", "BAJAJ-AUTO.NS", "DIVISLAB.NS", "UPL.NS", "ONGC.NS",
    "SHREECEM.NS", "JSWENERGY.NS", "TATACONSUM.NS", "PIDILITIND.NS", "SIEMENS.NS", "AMBUJACEM.NS", "VEDL.NS", "HAVELLS.NS", "ICICIPRULI.NS", "GAIL.NS",
    "IOC.NS", "DLF.NS", "CHOLAFIN.NS", "BEL.NS", "ABB.NS", "DABUR.NS", "MARICO.NS", "TVSMOTOR.NS", "TATACOMM.NS", "SRF.NS",
    "HAL.NS", "PAGEIND.NS", "COLPAL.NS", "POLYCAB.NS", "AUBANK.NS", "BERGEPAINT.NS", "MUTHOOTFIN.NS", "TRENT.NS", "PIIND.NS", "CONCOR.NS",
    "DALBHARAT.NS", "LTTS.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS", "MAXHEALTH.NS", "LTIM.NS", "JIOFIN.NS", "ZOMATO.NS", "PAYTM.NS",
    "NYKAA.NS", "DELHIVERY.NS", "AWL.NS", "LODHA.NS", "POONAWALLA.NS", "YESBANK.NS", "IDFCFIRSTB.NS", "GMRINFRA.NS", "RVNL.NS", "IRFC.NS"
]

def run_load_test():
    print(f"--- STARTING LOAD TEST ---")
    print(f"Portfolio Size: {len(SYMBOLS)} stocks")
    print(f"Simulations:    5,000 (Optimized Batch Mode)")
    print(f"Horizon:        60 Months")
    
    # Construct massive payload
    holdings = []
    for i, sym in enumerate(SYMBOLS):
        holdings.append({
            "symbol": sym,
            "quantity": 10 + i,
            "value": 5000 + (i * 100)
        })
        
    payload = {
        "portfolio_id": "load_test_100_v1",
        "holdings": holdings,
        "num_sims": 5000,
        "horizon_months": 60
    }
    
    start_time = time.time()
    
    try:
        print("\nSending request to AWS... (Fetching 100 symbols + 5,000 sims)")
        response = requests.post(
            API_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            },
            timeout=30 # Wait up to 30s
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            print("SUCCESS!")
            print(f"Total Response Time: {duration:.2f} seconds")
            
            result = response.json()
            print("-" * 40)
            print(f"Current Value:  INR {result['current_value']:,.2f}")
            print(f"Bull Case (5Y): INR {result['scenarios']['optimistic']['terminal_value']:,.2f}")
            print(f"Bear Case (5Y): INR {result['scenarios']['pessimistic']['terminal_value']:,.2f}")
            print(f"Prob. of Profit: {result['probability_scores']['probability_of_profit']}%")
            print("-" * 40)
            
        else:
            print(f"FAILED with Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("FAILED: Request timed out at 30 seconds.")
    except Exception as e:
        print(f"SYSTEM ERROR: {str(e)}")

if __name__ == "__main__":
    run_load_test()

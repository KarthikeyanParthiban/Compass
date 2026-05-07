import requests
import json
import logging
from datetime import datetime

# --- Configuration ---
# Your new high-speed Pure-Lambda URL (via API Gateway v2)
API_URL = "https://35w41kobie.execute-api.ap-south-1.amazonaws.com/default/v2"
API_KEY = "wwNacOkQ0o6jTocgeCDtAayvSFANpn9M5ZTU8qDy"

# Sample Portfolio for Testing
payload = {
    "portfolio_id": f"lambda_test_{datetime.now().strftime('%H%M%S')}",
    "holdings": [
        {"symbol": "RELIANCE.NS", "quantity": 50, "value": 73000},
        {"symbol": "TCS.NS", "quantity": 20, "value": 82000},
        {"symbol": "HDFCBANK.NS", "quantity": 35, "value": 61000}
    ],
    "num_sims": 2000,
    "horizon_months": 60
}

def run_test():
    print("\n[START] Testing Pure-Lambda Engine")
    print(f"URL: {API_URL}")
    print("-" * 50)
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        start_time = datetime.now()
        response = requests.post(
            API_URL, 
            json=payload, 
            headers={"x-api-key": API_KEY},
            timeout=30, 
            verify=False
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.json()
            print(f"DONE: Success! (Response Time: {duration:.2f}s)")
            print("-" * 50)
            print("FULL RESPONSE SCHEMA:")
            print(json.dumps(data, indent=2))
            print("-" * 50)
            
            scenarios = data['scenarios']
            print("5-Year Projections:")
            for key, info in scenarios.items():
                print(f"  {info['label']:<12}: INR {info['terminal_value']:>12,.2f} ({info['cagr_pct']:>5}% CAGR)")
            
            print("-" * 50)
            probs = data['probability_scores']
            print("Risk & Probability Metrics:")
            print(f"• Probability of Profit: {probs['probability_of_profit']}%")
            print(f"• Probability of Doubling: {probs['probability_of_doubling']}%")
            print(f"• Value at Risk (5% worst case): {probs['var_drawdown_pct']}% drawdown")
            print("-" * 50)

            # Monthly Trajectories Table
            print("\nMonthly Trajectories (All Scenarios):")
            print("Month   | Bear (Pessimistic) | Base (Expected)    | Bull (Optimistic)")
            print("-" * 70)
            
            pess = scenarios['pessimistic']['monthly_values']
            exp = scenarios['expected']['monthly_values']
            opt = scenarios['optimistic']['monthly_values']
            
            for i in range(len(pess)):
                print(f"{i:<7} | INR {pess[i]:>14,.2f} | INR {exp[i]:>14,.2f} | INR {opt[i]:>14,.2f}")

        else:
            print(f"FAIL: API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"ERROR: Connection Error: {str(e)}")
        print("\nTip: If you see an SSL error, try updating your 'certifi' package or check if your company firewall blocks Lambda URLs.")

if __name__ == "__main__":
    run_test()

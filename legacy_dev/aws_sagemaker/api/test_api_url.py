import requests
import json
import logging
from datetime import datetime

# Setup local logging to a file
logging.basicConfig(
    filename='api_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🚨 PASTE YOUR AWS API GATEWAY URL HERE 🚨
API_URL = "https://35w41kobie.execute-api.ap-south-1.amazonaws.com/default/Compass-MonteCarlo-Bridge"

# 🔑 PASTE YOUR API KEY HERE (from API Gateway -> API Keys)
API_KEY = "wwNacOkQ0o6jTocgeCDtAayvSFANpn9M5ZTU8qDy"

# The exact same test payload
payload = {
    "portfolio_id": "api_test_001",
    "holdings": [
        {"symbol": "SHRIRAMFIN.NS", "quantity": 158, "value": 150842},
        {"symbol": "SBIN.NS", "quantity": 10,  "value": 10524},
        {"symbol": "LLOYDSME.NS", "quantity": 28, "value": 49490}
    ],
    "num_sims": 1000,
    "horizon_months": 60
}

print(f"Sending request to: {API_URL}")
logging.info(f"REQUEST - URL: {API_URL} - Payload: {json.dumps(payload)}")

try:
    response = requests.post(
        API_URL, 
        json=payload, 
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        logging.info(f"RESPONSE - Status: 200 - CurrentValue: {result.get('current_value')}")
        print("\nAPI Call Successful!")
        print("-" * 40)
        print(f"Current Portfolio Value: INR {result['current_value']:,.2f}")
        print("-" * 40)
        
        scenarios = result['scenarios']
        print("5-Year Projections:")
        print(f"Bull Case (Optimistic): INR {scenarios['optimistic']['terminal_value']:,.2f}  (CAGR: {scenarios['optimistic']['cagr_pct']}%)")
        print(f"Base Case (Expected):   INR {scenarios['expected']['terminal_value']:,.2f}  (CAGR: {scenarios['expected']['cagr_pct']}%)")
        print(f"Bear Case (Pessimistic):INR {scenarios['pessimistic']['terminal_value']:,.2f}  (CAGR: {scenarios['pessimistic']['cagr_pct']}%)")
        print("-" * 40)
        
        probs = result['probability_scores']
        print("Risk & Probability Metrics:")
        print(f"• Probability of Profit: {probs['probability_of_profit']}%")
        print(f"• Probability of Doubling: {probs['probability_of_doubling']}%")
        print(f"• Value at Risk (5% worst case): {probs['var_drawdown_pct']}% drawdown")
        print("-" * 40)
        
        print("\nMonthly Trajectories (All Scenarios):")
        expected_data = scenarios['expected']['monthly_values']
        optimistic_data = scenarios['optimistic']['monthly_values']
        pessimistic_data = scenarios['pessimistic']['monthly_values']
        
        # Print header
        print(f"{'Month':<7} | {'Bear (Pessimistic)':<18} | {'Base (Expected)':<18} | {'Bull (Optimistic)':<18}")
        print("-" * 70)
        
        for i in range(len(expected_data)):
            bear = f"INR {pessimistic_data[i]:,.2f}"
            base = f"INR {expected_data[i]:,.2f}"
            bull = f"INR {optimistic_data[i]:,.2f}"
            print(f"{i:<7} | {bear:<18} | {base:<18} | {bull:<18}")
        
    else:
        logging.error(f"API ERROR - Status: {response.status_code} - Response: {response.text}")
        print(f"API Failed with status code: {response.status_code}")
        print("Response:", response.text)

except Exception as e:
    logging.error(f"SYSTEM ERROR: {str(e)}")
    print(f"Request failed. Did you paste your URL? Error: {e}")

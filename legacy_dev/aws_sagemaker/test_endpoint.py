import boto3
import json

# The static endpoint name we defined in deploy_sagemaker.py
ENDPOINT_NAME = "monte-carlo-api-serverless"
REGION = "ap-south-1"

# Initialize the SageMaker Runtime client
runtime_client = boto3.client('sagemaker-runtime', region_name=REGION)

# This is the test portfolio payload we will send to the API
payload = {
    "portfolio_id": "api_test_debug",
    "holdings": [
        {"symbol": "JIOFIN.NS", "quantity": 5, "value": 1243},
        {"symbol": "SBIN.NS", "quantity": 10,  "value": 10524},
        {"symbol": "LLOYDSME.NS", "quantity": 28, "value": 49490}
    ],
    "num_sims": 1000,
    "horizon_months": 60
}

print(f"Sending simulation request to endpoint: {ENDPOINT_NAME}...")

try:
    # Invoke the endpoint
    response = runtime_client.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType='application/json',
        Body=json.dumps(payload)
    )

    # Read and parse the response
    result = json.loads(response['Body'].read().decode())
    
    print("\nSimulation Successful!")
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

except Exception as e:
    print(f"\nError calling endpoint: {e}")
    print("Make sure your endpoint is fully 'InService' in the AWS Console before calling it.")

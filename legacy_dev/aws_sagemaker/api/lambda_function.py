import os
import json
import boto3

# Initialize the SageMaker Runtime client
# The region is usually automatically provided by the Lambda environment, 
# but we can hardcode it to be safe.
REGION = os.environ.get('AWS_REGION', 'ap-south-1')
sagemaker_client = boto3.client('sagemaker-runtime', region_name=REGION)

# The name of our deployed serverless endpoint
ENDPOINT_NAME = os.environ.get('ENDPOINT_NAME', 'monte-carlo-api-serverless')

from datetime import datetime

s3_client = boto3.client('s3', region_name=REGION)
LOGS_BUCKET = os.environ.get('LOGS_BUCKET', 'sagemaker-ap-south-1-006604849591')

def lambda_handler(event, context):
    """
    AWS Lambda bridge with integrated S3 persistent logging.
    Handles CORS and SageMaker invocation.
    """
    # 1. Handle CORS Preflight
    if event.get('httpMethod') == 'OPTIONS':
        return _build_response(200, {"message": "CORS Preflight OK"})
    
    start_ts = datetime.now()
    request_id = context.aws_request_id
    
    # 2. Extract Body
    try:
        body_str = event['body'] if 'body' in event and event['body'] else json.dumps(event)
        input_data = json.loads(body_str)
    except Exception as e:
        return _build_response(400, {"error": f"Invalid JSON: {str(e)}"})

    # 3. Call SageMaker
    try:
        sm_response = sagemaker_client.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='application/json',
            Body=body_str
        )
        result = json.loads(sm_response['Body'].read().decode('utf-8'))
        end_ts = datetime.now()
        
        # 4. Save LOG to S3 (Fail-safe)
        try:
            log_entry = {
                "timestamp": start_ts.isoformat(),
                "duration": (end_ts - start_ts).total_seconds(),
                "request": input_data,
                "response": result
            }
            log_key = f"api-logs/{start_ts.strftime('%Y-%m-%d')}/{start_ts.strftime('%H%M%S')}-{request_id}.json"
            s3_client.put_object(
                Bucket=LOGS_BUCKET,
                Key=log_key,
                Body=json.dumps(log_entry),
                ContentType='application/json'
            )
        except: pass
        
        return _build_response(200, result)
        
    except Exception as e:
        return _build_response(500, {"error": str(e)})

def _build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key,x-api-key,Authorization',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }

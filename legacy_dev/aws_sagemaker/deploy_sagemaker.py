import boto3
import os
import tarfile
from datetime import datetime
import json

# ── Configuration ────────────────────────────────────────────────────────────
ROLE_NAME = "SageMakerExecutionRole"
REGION = "ap-south-1"
ENDPOINT_NAME = "monte-carlo-api-serverless"
BUCKET_NAME = None # Will auto-detect or use default SageMaker bucket

sagemaker_client = boto3.client('sagemaker', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)
iam_client = boto3.client('iam')

# Get AWS Account ID
try:
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()["Account"]
except Exception as e:
    print(f"Error fetching AWS Account ID. Are your credentials configured? {e}")
    exit(1)

# Construct Role ARN manually to bypass iam:GetRole permission check
role_arn = f"arn:aws:iam::{account_id}:role/{ROLE_NAME}"

# Get Default Bucket
if not BUCKET_NAME:
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()["Account"]
    BUCKET_NAME = f"sagemaker-{REGION}-{account_id}"
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except Exception:
        try:
            s3_client.create_bucket(Bucket=BUCKET_NAME, CreateBucketConfiguration={'LocationConstraint': REGION})
        except Exception as e:
            print("\n❌ AWS PERMISSION ERROR:")
            print(f"Your AWS_CLI user does not have permission to create the S3 bucket '{BUCKET_NAME}'.")
            print("To fix this, go to AWS IAM -> Users -> AWS_CLI -> Add Permissions -> Attach 'AdministratorAccess'.")
            exit(1)

# ── Step 1: Package the model ────────────────────────────────────────────────
print("Packaging inference code...")
source_dir = "d:/Projects/Github/Compass/aws_sagemaker/inference"
tar_path = "model.tar.gz"

with tarfile.open(tar_path, "w:gz") as tar:
    tar.add(os.path.join(source_dir, "inference.py"), arcname="inference.py")
    tar.add(os.path.join(source_dir, "requirements.txt"), arcname="requirements.txt")

# ── Step 2: Upload to S3 ─────────────────────────────────────────────────────
print("Uploading to S3...")
s3_key = f"monte-carlo/model/model.tar.gz"
s3_client.upload_file(tar_path, BUCKET_NAME, s3_key)
model_data_url = f"s3://{BUCKET_NAME}/{s3_key}"
print(f"Uploaded to: {model_data_url}")

# ── Step 3: Create the Model ─────────────────────────────────────────────────
print("Creating SageMaker Model...")
# Use standard AWS Scikit-Learn Container for ap-south-1
# SKLearn 1.2-1 Python 3 container for ap-south-1
container_uri = "720646828776.dkr.ecr.ap-south-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3"

model_name = f"monte-carlo-model-{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
sagemaker_client.create_model(
    ModelName=model_name,
    ExecutionRoleArn=role_arn,
    PrimaryContainer={
        'Image': container_uri,
        'ModelDataUrl': model_data_url,
        'Environment': {
            'SAGEMAKER_PROGRAM': 'inference.py',
            'SAGEMAKER_SUBMIT_DIRECTORY': model_data_url,
            'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
            'SAGEMAKER_REGION': REGION
        }
    }
)

# ── Step 4: Create Endpoint Config (SERVERLESS) ──────────────────────────────
print("Creating Serverless Endpoint Configuration...")
config_name = f"monte-carlo-config-{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
sagemaker_client.create_endpoint_config(
    EndpointConfigName=config_name,
    ProductionVariants=[
        {
            'VariantName': 'AllTraffic',
            'ModelName': model_name,
            'ServerlessConfig': {
                'MemorySizeInMB': 2048,  # 2 GB RAM (Plenty for Monte Carlo math)
                'MaxConcurrency': 5      # Allow up to 5 simultaneous requests
            }
        }
    ]
)

# ── Step 5: Deploy the Endpoint ──────────────────────────────────────────────
print("Deploying Endpoint (this will take 5-10 minutes)...")
try:
    sagemaker_client.describe_endpoint(EndpointName=ENDPOINT_NAME)
    print(f"Endpoint '{ENDPOINT_NAME}' already exists. Updating it...")
    sagemaker_client.update_endpoint(
        EndpointName=ENDPOINT_NAME,
        EndpointConfigName=config_name
    )
    print("\nUpdate Initiated Successfully!")
except Exception:
    print(f"Creating new endpoint '{ENDPOINT_NAME}'...")
    sagemaker_client.create_endpoint(
        EndpointName=ENDPOINT_NAME,
        EndpointConfigName=config_name
    )
    print("\nDeployment Initiated Successfully!")
print(f"Endpoint Name: {ENDPOINT_NAME}")
print("\nNote: The endpoint will be in 'Creating' status in the AWS Console for a few minutes.")

# Cleanup local tar
if os.path.exists(tar_path):
    os.remove(tar_path)

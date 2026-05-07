import boto3
import subprocess
import os
import sys

# --- Configuration ---
REGION = "ap-south-1"
ACCOUNT_ID = "006604849591"
REPO_NAME = "compass-lambda-engine"
FUNCTION_NAME = "Compass-MonteCarlo-Engine-Serverless"
# Reusing the existing role from our bridge lambda
ROLE_ARN = "arn:aws:iam::006604849591:role/service-role/Compass-MonteCarlo-Bridge-role-unsogtnb"

def deploy():
    print("--- Starting All-Lambda Deployment ---")
    
    # 1. Build and Push Docker Image
    ecr_uri = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/{REPO_NAME}"
    
    try:
        print(f"Logging into ECR...")
        login_cmd = f"aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com"
        subprocess.run(login_cmd, shell=True, check=True)
        
        print(f"Building Docker Image (AMD64 Legacy Format)...")
        # Disabling provenance and forcing amd64 ensures AWS Lambda compatibility
        subprocess.run(f"docker build --platform linux/amd64 --provenance=false -t {REPO_NAME} ./lambda_engine", shell=True, check=True)
        
        print(f"Tagging and Pushing Image...")
        subprocess.run(f"docker tag {REPO_NAME}:latest {ecr_uri}:latest", shell=True, check=True)
        
        # Ensure Repo exists
        ecr = boto3.client('ecr', region_name=REGION)
        try:
            ecr.create_repository(repositoryName=REPO_NAME)
        except ecr.exceptions.RepositoryAlreadyExistsException:
            pass
            
        subprocess.run(f"docker push {ecr_uri}:latest", shell=True, check=True)
        print("Image pushed to ECR successfully.")
        
    except Exception as e:
        print(f"Docker/ECR Error: {str(e)}")
        sys.exit(1)

    # 2. Create or Update Lambda Function
    client = boto3.client('lambda', region_name=REGION)
    
    try:
        print(f"Checking for existing function {FUNCTION_NAME}...")
        client.get_function(FunctionName=FUNCTION_NAME)
        
        print(f"Updating function code...")
        client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ImageUri=f"{ecr_uri}:latest"
        )
        print("Lambda code updated.")
        
    except client.exceptions.ResourceNotFoundException:
        print(f"Creating new function {FUNCTION_NAME}...")
        client.create_function(
            FunctionName=FUNCTION_NAME,
            PackageType='Image',
            Code={'ImageUri': f"{ecr_uri}:latest"},
            Role=ROLE_ARN,
            Timeout=29, # API Gateway limit
            MemorySize=2048 # High memory for faster math
        )
        print("Lambda function created.")
    
    except Exception as e:
        print(f"Lambda Error: {str(e)}")
        sys.exit(1)

    print("\n--- DEPLOYMENT COMPLETE ---")
    print(f"Function Name: {FUNCTION_NAME}")

if __name__ == "__main__":
    deploy()

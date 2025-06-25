import boto3
import os

def verify_aws_credentials(access_key=None, secret_key=None):
    """
    Verify AWS credentials and print account info
    """
    try:
        # Create STS client with explicit credentials if provided
        if access_key and secret_key:
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='us-east-1'  # Specify your region
            )
        else:
            # Use environment variables or AWS credentials file
            sts_client = boto3.client('sts')
        
        # Get caller identity
        response = sts_client.get_caller_identity()
        # print("Credentials are valid!")
        # print(f"Account ID: {response['Account']}")
        # print(f"User/Role ARN: {response['Arn']}")
        return True
        
    except Exception as e:
        # print(f"Credential verification failed: {str(e)}")
        return False

def check_organizations_access():
    """
    Check if we have access to AWS Organizations
    """
    try:
        org_client = boto3.client('organizations')
        org_client.describe_organization()
        # print("Successfully accessed AWS Organizations!")
        return True
    except Exception as e:
        # print(f"Organizations access check failed: {str(e)}")
        return False

# Check current environment variables
# print("Current AWS Environment Variables:")
# print(f"AWS_ACCESS_KEY_ID: {'Set' if os.getenv('AWS_ACCESS_KEY_ID') else 'Not Set'}")
# print(f"AWS_SECRET_ACCESS_KEY: {'Set' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'Not Set'}")
# print(f"AWS_SESSION_TOKEN: {'Set' if os.getenv('AWS_SESSION_TOKEN') else 'Not Set'}")
# print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION', 'Not Set')}")

# Verify credentials
# verify_aws_credentials()
# check_organizations_access()
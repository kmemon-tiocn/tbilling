import boto3
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import logging
import time
import os
from pathlib import Path
import environ

env = environ.Env(
    DEBUG=(bool, True)
)
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

class AWSAccountManager:
    def __init__(self, access_key, secret_key, region: str = 'us-east-1'):
        """
        Initialize the AWS Billing Manager with master account credentials.
        
        Args:
            access_key (str): AWS ACCESS KEY
            secret_key (str): AWS SECRET KEY
            region (str): AWS Region (default: us-east-1)
        """
        # print('.'*15, access_key, secret_key)
        self.access_key = access_key
        self.secret_key = secret_key
        self.master_account_id = self.get_master_account_id()
        self.region = region
        
          # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize AWS clients
        try:
            session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            ) 
            self.org_client = session.client('organizations', region_name=region)
            self.ce_client = session.client('ce', region_name=region)
            self.sts_client = session.client('sts', region_name=region)
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise
    
    def get_master_account_id(self):
        # Create STS client
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
        
        try:
            # Get the caller identity
            response = sts_client.get_caller_identity()
            account_id = response['Account']
            # print(f"Your AWS Account ID is: {account_id}")
            return account_id
        except Exception as e:
            # print(f"Error: {str(e)}")
            return None
        
    def invite_account(self, account_id: str, target_email: str = None) -> Dict:
        """
        Invite an existing AWS account to join the organization.
        
        Args:
            account_id (str): AWS Account ID to invite
            target_email (str, optional): Email address to send invitation
            
        Returns:
            Dict: Invitation details including status
        """
        try:
            # Create the invitation
            params = {'Target': {'Type': 'ACCOUNT', 'Id': account_id}}
            if target_email:
                params['TargetEmail'] = target_email

            response = self.org_client.invite_account_to_organization(**params)
            
            invitation = response['Handshake']
            self.logger.info(f"Invitation sent to account {account_id}")
            
            return {
                'invitation_id': invitation['Id'],
                'account_id': account_id,
                'status': invitation['State']
            }
        except Exception as e:
            if "already a member" in str(e):
                return {
                    'invitation_id': None,
                    'account_id': account_id,
                    'status': 'ACCEPTED'
                }
            elif "already exists" in str(e):
                return {
                    'invitation_id': None,
                    'account_id': account_id,
                    'status': 'OPEN'
                }
            else:
                self.logger.error(f"Error inviting account: {str(e)}")
                raise

    def check_invitation_status(self, invitation_id: str) -> str:
        """
        Check the status of an account invitation.
        
        Args:
            invitation_id (str): The invitation ID to check
            
        Returns:
            str: Current status of the invitation
        """
        try:
            response = self.org_client.describe_handshake(
                HandshakeId=invitation_id
            )
            return response['Handshake']['State']
        except Exception as e:
            self.logger.error(f"Error checking invitation status: {str(e)}")
            raise

    def list_pending_invitations(self) -> List[Dict]:
        """
        List all pending invitations in the organization.
        
        Returns:
            List[Dict]: List of pending invitations
        """
        try:
            response = self.org_client.list_handshakes_for_organization(
                Filter={'ActionType': 'INVITE'}
            )
            return response['Handshakes']
        except Exception as e:
            self.logger.error(f"Error listing pending invitations: {str(e)}")
            raise

    def setup_billing_access(self, account_id: str) -> bool:
        """
        Setup billing access and monitoring for a member account.
        
        Args:
            account_id (str): The member account ID
            
        Returns:
            bool: True if setup successful
        """
        try:
            # Enable billing access
            self.org_client.enable_aws_service_access('aws-service-name')
            
            # Setup default billing alerts
            self.ce_client.update_cost_allocation_tags_status(
                CostAllocationTagsStatus=[{
                    'TagKey': 'Environment',
                    'Status': 'Active'
                }]
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting up billing access: {str(e)}")
            raise

    def create_account(self, account_name: str, email: str, role_name: str = "OrganizationAccountAccessRole") -> Dict:
        """
        Create a new AWS account in the organization.
        
        Args:
            account_name (str): Name for the new account
            email (str): Email address for the root user of the new account
            role_name (str): Name of the IAM role to create (default: OrganizationAccountAccessRole)
            
        Returns:
            Dict: Details of the created account
        """
        try:
            response = self.org_client.create_account(
                Email=email,
                AccountName=account_name,
                RoleName=role_name,
                IamUserAccessToBilling='ALLOW'
            )
            
            # Get the create account status
            create_status = response['CreateAccountStatus']
            request_id = create_status['Id']
            
            # Wait for account creation to complete
            while True:
                status_response = self.org_client.describe_create_account_status(
                    CreateAccountRequestId=request_id
                )
                status = status_response['CreateAccountStatus']['State']
                
                if status == 'SUCCEEDED':
                    account_id = status_response['CreateAccountStatus']['AccountId']
                    self.logger.info(f"Account created successfully. Account ID: {account_id}")
                    return {
                        'account_id': account_id,
                        'account_name': account_name,
                        'email': email,
                        'role_name': role_name
                    }
                elif status == 'FAILED':
                    failure_reason = status_response['CreateAccountStatus'].get('FailureReason', 'Unknown')
                    raise Exception(f"Account creation failed: {failure_reason}")
                
                time.sleep(10)  # Wait before checking status again
                
        except Exception as e:
            self.logger.error(f"Error creating account: {str(e)}")
            raise

    def get_linked_accounts(self) -> List[Dict]:
        """
        Retrieve all linked accounts in the organization.
        
        Returns:
            List[Dict]: List of account details including ID and name
        """
        try:
            accounts = []
            paginator = self.org_client.get_paginator('list_accounts')
            
            for page in paginator.paginate():
                for account in page['Accounts']:
                    if account['Status'] == 'ACTIVE':
                        accounts.append({
                            'id': account['Id'],
                            'name': account['Name'],
                            'email': account['Email']
                        })
            
            return accounts
        except Exception as e:
            self.logger.error(f"Error fetching linked accounts: {str(e)}")
            raise

    def get_cost_and_usage(self, start_date: str, end_date: str, 
                          account_id: Optional[str] = None,
                          granularity: str = 'MONTHLY') -> Dict:
        # print('-'*15, start_date, end_date)
        """
        Get cost and usage data for specified period and account.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            account_id (str, optional): Specific account ID to query
            granularity (str): Time granularity (DAILY|MONTHLY)
            
        Returns:
            Dict: Cost and usage data
        """
        # try:
        filters = {
            'TimePeriod': {
                'Start': start_date,
                'End': end_date
            },
            'Granularity': granularity,
            'Metrics': ['UnblendedCost', 'UsageQuantity'],
            'GroupBy': [
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}
            ]
        }
        
        if account_id:
            filters['Filter'] = {
                'Dimensions': {
                    'Key': 'LINKED_ACCOUNT',
                    'Values': [account_id]
                }
            }
        
        results = self.ce_client.get_cost_and_usage(**filters)
        return results
        # except Exception as e:
        #     self.logger.error(f"Error fetching cost and usage data: {str(e)}")
        #     raise

    def generate_billing_report(self, date):
        """
        Generate a comprehensive billing report for all accounts.
        
        Args:
            date (str): Start date in YYYY-MM-DD format
            
        Returns:
            pd.DataFrame: Billing report as a pandas DataFrame
        """
        # try:
        # Get all accounts
        accounts = self.get_linked_accounts()
        # print(accounts)
        account_map = {acc['id']: acc['name'] for acc in accounts}
        account_email_map = {acc['id']: acc['email'] for acc in accounts}
        
        # Get cost data
        cost_data = self.get_cost_and_usage(date, (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
        
        # Process the data
        rows = []
        for result in cost_data['ResultsByTime']:
            # print('Result:', result, '.'*10)
            time_period = result['TimePeriod']['Start']
            
            for group in result['Groups']:
                service = group['Keys'][0]
                account_id = group['Keys'][1]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                cost_unit = group['Metrics']['UnblendedCost']['Unit']
                usage = group['Metrics']['UsageQuantity']['Amount']
                usage_unit = group['Metrics']['UsageQuantity']['Unit']
                
                rows.append({
                    'Date': time_period,
                    'Account ID': account_id,
                    'Account Name': account_map.get(account_id, 'Unknown'),
                    'Account Email': account_email_map.get(account_id, 'Unknown'),
                    'Service': service,
                    'Cost': cost,
                    'Cost Unit': cost_unit,
                    'Usage': usage,
                    'Usage Unit': usage_unit
                })
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        return df
        # return rows
        # except Exception as e:
        #     self.logger.error(f"Error generating billing report: {str(e)}")
        #     raise

    def export_report_to_csv(self, df: pd.DataFrame, filename: str):
        """
        Export billing report to CSV file.
        
        Args:
            df (pd.DataFrame): Billing report DataFrame
            filename (str): Output filename
        """
        try:
            df.to_csv(filename, index=False)
            self.logger.info(f"Report exported successfully to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting report to CSV: {str(e)}")
            raise

    def get_account_cost_alerts(self, threshold: float) -> List[Dict]:
        """
        Check for accounts exceeding specified cost threshold.
        
        Args:
            threshold (float): Cost threshold in USD
            
        Returns:
            List[Dict]: List of accounts exceeding threshold
        """
        try:
            # Get current month's data
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            cost_data = self.get_cost_and_usage(start_date, end_date)
            alerts = []
            
            for result in cost_data['ResultsByTime']:
                for group in result['Groups']:
                    account_id = group['Keys'][1]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if cost > threshold:
                        alerts.append({
                            'account_id': account_id,
                            'cost': cost,
                            'threshold': threshold
                        })
            
            return alerts
        except Exception as e:
            self.logger.error(f"Error checking cost alerts: {str(e)}")
            raise
        
    def get_account_id_by_email(self, email):
        """Retrieve account ID by email."""
        accounts = self.org.list_accounts()['Accounts']
        for acct in accounts:
            if acct['Email'].lower() == email.lower() and acct['Status'] == 'ACTIVE':
                return acct['Id']
        return None

    def move_account_to_ou(self, account_id):
        """Move the account to the specified OU directly."""
        try:
            # Directly move the account to the provided OU ID
            self.org.move_account(
                AccountId=account_id,
                SourceParentId="r-56af",  # Root ID (you can set this as the root or parent ID)
                DestinationParentId=self.ou_id  # Move directly to the provided OU ID
            )
            logging.info(f"✅ Moved account {account_id} to OU '{self.ou_id}'")
        except Exception as e:
            logging.error(f"❌ Error moving account {account_id} to OU: {e}")

    def enforce_for_email(self, email):
        """Check if the email has a pending invitation and enforce actions."""
        try:
            # Move the account to the specified OU
            account_id = self.get_account_id_by_email(email)
            self.move_account_to_ou(account_id)

            logging.info(f"✅ Enforcement complete for {email}")
            return True
        except Exception as e:
            logging.error(f"❌ Enforcement failed for {email}: {e}")
            return False

if __name__ == "__main__":
    # print('.'*15, env('AWS_ACCESS_KEY_ID'), env('AWS_SECRET_ACCESS_KEY'))
    # Initialize the billing manager
    billing_manager = AWSAccountManager(env('AWS_ACCESS_KEY_ID'), env('AWS_SECRET_ACCESS_KEY'))
    
    # Set date range for report
    start_date = "2025-03-11"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    hello = billing_manager.get_linked_accounts()
    print('-'*25, hello)
    # # Generate and export billing report
    report_df = billing_manager.generate_billing_report(start_date)
    print(report_df)
    billing_manager.export_report_to_csv(report_df, 'aws_billing_report.csv')
    
#     # Check for cost alerts
#     alerts = billing_manager.get_account_cost_alerts(threshold=1000.0)
#     for alert in alerts:
#         print(f"Alert: Account {alert['account_id']} exceeded threshold of ${alert['threshold']}")
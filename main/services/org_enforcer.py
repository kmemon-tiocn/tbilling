import boto3
import logging

class OrgEnforcer:
    def __init__(self, access_key, secret_key, region: str = 'us-east-1', ou_id: str = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.org = session.client("organizations")
        self.ou_id = ou_id 
        
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

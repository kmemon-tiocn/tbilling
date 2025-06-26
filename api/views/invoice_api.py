import os
import shutil
import logging
from django.conf import settings

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.core.files import File
from datetime import datetime, timedelta

from main.services import AWSAccountManager

from main.models import AwsAccount, AwsCostManagement, RootInvoice
from main.helpers.invoice_service import S3FileFetcher, get_this_month_csv_bills


class GetInvoiceAPIView(APIView):
    """API to check if billing data exists. If not, fetches CSV files and creates invoices."""

    def get(self, request):
        try:
            # Response data initialization
            response_data = []
            today = datetime.today()
            bill_start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            bill_end_date = today.replace(day=1)
            invoice_date = today.date()

            # Check if an invoice already exists for the current billing period
            existing_invoice = RootInvoice.objects.filter(
                bill_start_date=bill_start_date,
                bill_end_date=bill_end_date
            ).exists()

            if existing_invoice:
                response_data.append({"message": "Invoice already exists."})
            else:
                # ✅ Initialize S3 Fetcher using credentials from settings
                s3_fetcher = S3FileFetcher()  # No need to pass organization anymore

                # Fetch the CSV files from S3
                extracted_csv_files = get_this_month_csv_bills(s3_fetcher)

                if not extracted_csv_files:
                    response_data.append({"message": "No CSV files found."})
                else:
                    saved_invoices = []
                    extracted_path = f"./extracted_csvs/"

                    # Process and save invoices
                    for csv_file in extracted_csv_files:
                        # ✅ Ensure file exists before proceeding
                        if not os.path.exists(csv_file):
                            logging.error(f"CSV file not found before saving: {csv_file}")
                            continue  # Skip this file but continue processing others

                        try:
                            with open(csv_file, 'rb') as file_data:
                                invoice = RootInvoice.objects.create(
                                    invoice_file=File(file_data, name=os.path.basename(csv_file)),
                                    invoice_date=invoice_date,
                                    bill_start_date=bill_start_date,
                                    bill_end_date=bill_end_date
                                )
                                saved_invoices.append(invoice.invoice_file.url)
                        except Exception as e:
                            logging.error(f"❌ Failed to save invoice: {str(e)}")
                            return Response({"error": f"Failed to save invoice: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                    # ✅ Only delete the extracted folder if invoices were successfully created
                    if saved_invoices and os.path.exists(extracted_path):
                        shutil.rmtree(extracted_path, ignore_errors=True)
                        logging.info(f"🗑️ Deleted extracted folder")

                    response_data.append({"invoices": saved_invoices})

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logging.error(f"🚨 Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SyncCostManagementAPIView(APIView):
    def get(self, request):
        try:
            # get_date (format = YYYY-MM-DD)
            start_date = request.query_params.get("start_date", None)
            
            if not start_date:
                today = datetime.today().date()
                start_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
                
            # Fetch AWS credentials and settings from the environment
            aws_access_key_id = settings.AWS_ACCESS_KEY_ID
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY

            if not aws_access_key_id or not aws_secret_access_key:
                return Response({"error": "AWS credentials are missing in settings."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Initialize AWSAccountManager with the global credentials
                billing_manager = AWSAccountManager(aws_access_key_id, aws_secret_access_key)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
           
            
            # Generate the billing report (the report is expected to be a JSON dict)
            report = billing_manager.generate_billing_report(start_date)

            # Parse the JSON report and update or create records
            # Expected keys in the JSON: "Date", "Account ID", "Account Name", "Account Email",
            # "Service", "Cost", "Cost Unit", "Usage", "Usage Unit"
            dates = report.get("Date", [])
            account_ids = report.get("Account ID", [])
            account_names = report.get("Account Name", [])
            account_emails = report.get("Account Email", [])
            services = report.get("Service", [])
            costs = report.get("Cost", [])
            cost_units = report.get("Cost Unit", [])
            usages = report.get("Usage", [])
            usage_units = report.get("Usage Unit", [])

            num_records = len(dates)
            for i in range(num_records):
                # Convert the date string to a date object
                billing_date = datetime.strptime(dates[i], "%Y-%m-%d").date()


                aws_account = AwsAccount.objects.filter(account_id=account_ids[i]).first()
                if not aws_account:
                     aws_account = AwsAccount.objects.create(account_id=account_ids[i], name=f"AWS Account {aws_account}")

    
                # Use update_or_create to insert or update the record based on composite key:
                # (billing_date, account_id, service)
                AwsCostManagement.objects.update_or_create(
                    billing_date=billing_date,
                    account_id=account_ids[i],
                    service=services[i],
                    defaults={
                        "aws_account": aws_account,
                        "account_name": account_names[i],
                        "account_email": account_emails[i],
                        "cost": costs[i],
                        "cost_unit": cost_units[i],
                        "usage": usages[i],
                        "usage_unit": usage_units[i]
                    }
                )

            return Response({"message": "Success"}, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"🚨 Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

import pandas as pd
import os
from django.db import transaction
from main.models import AwsAccount, Service, AccountService, AWSAccountInvoice
from datetime import datetime, timedelta
import math
from django.db.models.signals import post_save

def handle_nan(value):
    if isinstance(value, float) and (math.isnan(value) or value == 'NaN'):
        return 0.0
    return value


def process_invoice_csv_data(invoice):
    try:
        csv_file_path = invoice.invoice_file.path
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV file not found: {csv_file_path}")
            return

        df = pd.read_csv(csv_file_path, low_memory=False, dtype=str)

        existing_accounts = {acc.account_id: acc for acc in AwsAccount.objects.all()}
        existing_services = {f"{srv.name}-{srv.region}": srv for srv in Service.objects.all()}

        new_accounts = {}
        new_services = {}
        bulk_insert_data = []

        def clean_date(date_str):
            try:
                if pd.isna(date_str) or date_str.strip() == "":
                    return None
                return datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
            except Exception as e:
                print(f"⚠️ Error parsing date: {date_str} - {e}")
                return None

        def format_float(value):
            try:
                num = pd.to_numeric(value, errors='coerce')
                return float(format(num, ".10f")) if not pd.isna(num) else 0.0
            except Exception:
                return 0.0

        each_aws_account_total_bill_dict = {}

        for _, row in df.iterrows():
            try:
                aws_account_id = str(row.get('lineItem/UsageAccountId', '')).strip()
                service_name = str(row.get('product/ProductName', '')).strip()
                
                if service_name == "nan" or service_name == "NaN" or service_name == None:
                    service_name = str(row.get('lineItem/LineItemDescription', '')).strip()
                    if service_name == "nan" or service_name == "NaN" or service_name == None:
                        service_name = "Unknown Service"
                    
                region = str(row.get('product/region', 'us-east-1')).strip() or "us-east-1"
                
                if region == "nan" or region == "NaN" or region == None:
                    region = "global"

                usage_start_date = clean_date(row.get('lineItem/UsageStartDate', ''))
                usage_end_date = clean_date(row.get('lineItem/UsageEndDate', ''))

                if aws_account_id in existing_accounts:
                    aws_account = existing_accounts[aws_account_id]
                elif aws_account_id in new_accounts:
                    aws_account = new_accounts[aws_account_id]
                else:
                    aws_account = AwsAccount(account_id=aws_account_id, name=f"AWS Account {aws_account_id}")
                    new_accounts[aws_account_id] = aws_account

                service_key = f"{service_name}-{region}"
                if service_key in existing_services:
                    service = existing_services[service_key]
                elif service_key in new_services:
                    service = new_services[service_key]
                else:
                    service = Service(name=service_name, region=region)
                    new_services[service_key] = service

                bulk_insert_data.append(AccountService(
                    aws_account=aws_account,
                    service=service,
                    invoice=invoice,
                    blended_cost=handle_nan(format_float(row.get('lineItem/BlendedCost', 0.0))),
                    usage_amount=handle_nan(format_float(row.get('lineItem/UsageAmount', 0.0))),
                    unblendend_cost=handle_nan(format_float(row.get('lineItem/UnblendedCost', 0.0))),
                    usage_start_date=usage_start_date,
                    usage_end_date=usage_end_date,
                    product_description=row.get('product/description', ''),
                    tax_type=row.get('lineItem/TaxType', ''),
                    line_item_id=row.get('identity/LineItemId', ''),
                    product_code=row.get('lineItem/ProductCode', ''),
                    currency_code=row.get('lineItem/CurrencyCode', 'USD'),
                    public_on_demand_cost_pricing=handle_nan(row.get('pricing/publicOnDemandRate', 0.0)),
                    usage_unit_pricing=row.get('pricing/unit', ''),
                    usage_term_pricing=row.get('pricing/term', ''),
                    public_on_demand_rate_pricing=handle_nan(row.get('pricing/publicOnDemandCost', 0.0)),
                    savings_plan_used_commitment=handle_nan(row.get('savingsPlan/UsedCommitment', 0.0)),
                    savings_plan_savings_plan_rate=handle_nan(row.get('savingsPlan/SavingsPlanRate', 0.0)),
                    savings_plan_total_commitment_to_date=handle_nan(row.get('savingsPlan/TotalCommitmentToDate', 0.0)),
                    savings_plan_savings_plan_effective_cost=handle_nan(row.get('savingsPlan/SavingsPlanEffectiveCost', 0.0)),
                    savings_plan_savings_plan_arn=row.get('savingsPlan/SavingsPlanARN', ''),
                    savings_plan_recurring_commitment_for_billing_period=handle_nan(row.get('savingsPlan/RecurringCommitmentForBillingPeriod', 0.0)),
                    savings_plan_amortized_upfront_commitment_for_billing_period=handle_nan(row.get('savingsPlan/AmortizedUpfrontCommitmentForBillingPeriod', 0.0))
                ))
                
                each_aws_account_total_bill_dict[aws_account_id] = each_aws_account_total_bill_dict.get(aws_account_id, 0.0) + format_float(row.get('lineItem/BlendedCost', 0.0))

            except Exception as e:
                print(f"⚠️ Skipping row due to error: {e}")

        with transaction.atomic():
            if new_accounts:
                AwsAccount.objects.bulk_create(new_accounts.values(), ignore_conflicts=True)
                existing_accounts.update({acc.account_id: acc for acc in AwsAccount.objects.all()})

            if new_services:
                Service.objects.bulk_create(new_services.values(), ignore_conflicts=True)
                existing_services.update({f"{srv.name}-{srv.region}": srv for srv in Service.objects.all()})

            for account_service in bulk_insert_data:
                account_service.aws_account = existing_accounts[account_service.aws_account.account_id]
                service_key = f"{account_service.service.name}-{account_service.service.region}"
                account_service.service = existing_services[service_key]

            created_objs  = AccountService.objects.bulk_create(bulk_insert_data)
            for obj in created_objs:
                post_save.send(sender=AccountService, instance=obj, created=True)



            for aws_account_id, total_bill in each_aws_account_total_bill_dict.items():
                aws_account = existing_accounts[aws_account_id]
                aws_invoice, created = AWSAccountInvoice.objects.get_or_create(
                    aws_account=aws_account,
                    bill_start_date=invoice.bill_start_date,
                    bill_end_date=invoice.bill_end_date,
                    defaults={'total_ammount': total_bill, 'invoice_date': invoice.invoice_date}
                )
                if not created:
                    aws_invoice.total_ammount = total_bill
                    aws_invoice.save()

        print(f"✅ Successfully processed {len(bulk_insert_data)} rows from {csv_file_path}")

    except Exception as e:
        print(f"❌ Failed to process invoice {invoice.id}: {e}")

from django.db.models.signals import post_save
from django.dispatch import receiver
from main.models import RootInvoice, AwsAccount, AwsCostManagement, MonthlyCostByAccount, AccountService
from django.conf import settings
from django.db.models import Sum
from main.utils import process_invoice_csv_data
from main.services import AWSAccountManager

@receiver(post_save, sender=RootInvoice, weak=False)
def invoice_created_handler(sender, instance, created, **kwargs):
    """
    Signal triggered when an RootInvoice is created.
    Processes the invoice CSV immediately after save.
    """
    if created:
        process_invoice_csv_data(instance)



@receiver(post_save, sender=AwsAccount, weak=False)
def account_created_handler(sender, instance, created, **kwargs):
    if created:
        aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY

        account_manager = AWSAccountManager(aws_access_key_id, aws_secret_access_key)
        invite_sent = account_manager.invite_account(instance.account_id)

        if invite_sent:
            status = invite_sent['status']
            inviation_id = invite_sent['invitation_id']

            instance.invitation_status = status
            instance.invitation_id = inviation_id
            instance.save()


@receiver(post_save, sender=AwsCostManagement)
def update_monthly_costs(sender, instance, created, **kwargs):
    if not created:
        return  # Process only on creation

    billing_month = instance.billing_date.replace(day=1)
    
    aws_account = instance.aws_account

    # Validate customer existence
    customer = getattr(aws_account, 'customer', None)
    if not customer:
        return  # Skip if AWS account has no customer

    # Validate organization existence
    organization = getattr(customer, 'organization', None)
    if not organization:
        return  # Skip if customer has no organization

    service = instance.service

    # Update MonthlyCostByAccount
    account_cost, _ = MonthlyCostByAccount.objects.get_or_create(
        aws_account=aws_account, month=billing_month.month
    )
    account_total = AwsCostManagement.objects.filter(
        aws_account=aws_account,
        billing_date__year=billing_month.year,
        billing_date__month=billing_month.month
    ).aggregate(total=Sum('cost'))['total'] or 0
    account_cost.total_cost = account_total
    account_cost.save()
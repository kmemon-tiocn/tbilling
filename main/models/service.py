from django.db import models
from main.models import *
from .core import *

GENERIC_UNIT_CHOICES = (
    ("Flat", "Flat"),
    ("Percentage", "Percentage"),
)

class Service(BaseModel):
    name = models.CharField(max_length=50)
    region = models.CharField(max_length=50, default="us-east-1", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "AWS Service"
        verbose_name_plural = "AWS Services"
        constraints = [
            models.UniqueConstraint(fields=['name', 'region'], name='unique_service_region')
        ]

    def __str__(self):
        return self.name + ' - ' + str(self.region)
    


class AccountService(BaseModel):
    aws_account = models.ForeignKey(AwsAccount, on_delete=models.CASCADE, related_name='account_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='account_services')
    
    invoice = models.ForeignKey(RootInvoice, on_delete=models.CASCADE)

    blended_cost = models.FloatField(default=0) #csv_column_name = lineItem/BlendedCost
    usage_amount = models.FloatField(default=0)  #csv_column_name = lineItem/UsageAmount
    unblendend_cost = models.FloatField(default=0) #csv_column_name = lineItem/UnblendedCost
    usage_start_date = models.DateField(null=True, blank=True) #csv_column_name = lineItem/UsageStartDate
    usage_end_date = models.DateField(null=True, blank=True) #csv_column_name = lineItem/UsageEndDate
    product_description = models.TextField(blank=True, null=True) #csv_column_name = product/description
    tax_type = models.CharField(max_length=255, blank=True, null=True) #csv_column_name = lineItem/TaxType
    line_item_id = models.CharField(max_length=255, blank=True, null=True)  #csv_column_name = identity/LineItemId
    product_code = models.CharField(max_length=255, blank=True, null=True)  #csv_column_name = lineItem/ProductCode
    currency_code = models.CharField(max_length=10, default='USD', blank=True, null=True) #csv_column_name = lineItem/CurrencyCode


    public_on_demand_cost_pricing = models.FloatField(default=0) #csv_column_name = pricing/publicOnDemandRate
    usage_unit_pricing = models.CharField(max_length=255, blank=True, null=True) #csv_column_name = pricing/unit
    usage_term_pricing = models.CharField(max_length=255, blank=True, null=True) #csv_column_name = pricing/term
    public_on_demand_rate_pricing = models.FloatField(default=0) #csv_column_name = pricing/publicOnDemandCost
    
    savings_plan_used_commitment = models.FloatField(default=0) #csv_column_name = savingsPlan/UsedCommitment
    savings_plan_savings_plan_rate = models.FloatField(default=0) #csv_column_name = savingsPlan/SavingsPlanRate
    savings_plan_total_commitment_to_date = models.FloatField(default=0) #csv_column_name = savingsPlan/TotalCommitmentToDate
    savings_plan_savings_plan_effective_cost = models.FloatField(default=0) #csv_column_name = savingsPlan/SavingsPlanEffectiveCost
    savings_plan_savings_plan_arn = models.CharField(max_length=255, blank=True, null=True) #csv_column_name = savingsPlan/SavingsPlanARN
    savings_plan_recurring_commitment_for_billing_period = models.FloatField(default=0) #csv_column_name = savingsPlan/RecurringCommitmentForBillingPeriod
    savings_plan_amortized_upfront_commitment_for_billing_period = models.FloatField(default=0) #csv_column_name = savingsPlan/AmortizedUpfrontCommitmentForBillingPeriod

    extra_rate_type = models.CharField(max_length=50, choices=GENERIC_UNIT_CHOICES, default='Percentage')
    extra_rate_value = models.FloatField(default=0)


    class Meta:
        verbose_name = "Account Service"
        verbose_name_plural = "Account Services"
        indexes = [
            models.Index(fields=['aws_account', 'invoice']),  # index on aws_account and invoice
            models.Index(fields=['usage_end_date']),  # index on usage_end_date
        ]
    
    def __str__(self):
        return self.aws_account.name + ' - ' + self.service.name


    
class AwsCostManagement(BaseModel):
    aws_account = models.ForeignKey(AwsAccount, on_delete=models.CASCADE)

    billing_date = models.DateField()
    account_id = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    account_email = models.CharField(max_length=255, null=True, blank=True)
    service = models.CharField(max_length=255)
    cost = models.FloatField(default=0)
    cost_unit = models.CharField(max_length=25)
    usage = models.FloatField(default=0)
    usage_unit = models.CharField(max_length=25, default='-')

    class Meta:
        verbose_name = "Cost Management"
        verbose_name_plural = "Cost Managements"

    def __str__(self):
        return f"{self.aws_account.account_id} - {self.account_id} - {self.service} - {str(self.billing_date)}"



class MonthlyCostByAccount(BaseModel):
    aws_account = models.ForeignKey(AwsAccount, on_delete=models.CASCADE, related_name='monthly_cost_by_account')
    month = models.DateField()
    total_cost = models.FloatField(default=0)

    class Meta:
        verbose_name = "Monthly Cost by Account"
        verbose_name_plural = "Monthly Costs by Account"

    def __str__(self):
        return f"{self.aws_account.account_id} - {str(self.month)} - {self.total_cost}"
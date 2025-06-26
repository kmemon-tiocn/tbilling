from django.db import models
import datetime
import random

from .core import *

class RootInvoice(BaseModel):
    invoice_file = models.FileField(upload_to='invoice/', blank=True, null=True)
    invoice_date = models.DateField()
    bill_start_date = models.DateField()
    bill_end_date = models.DateField()

    class Meta:
        verbose_name = "Root Invoice"
        verbose_name_plural = "Root Invoices"

    def __str__(self):
        return f"Invoice Dae: {self.invoice_date} - Bill Start {self.bill_start_date} - Bill End: {self.bill_end_date}"
    
    
class AWSAccountInvoice(BaseModel):
    aws_account = models.ForeignKey(AwsAccount, on_delete=models.CASCADE, related_name='aws_account_invoices')
    total_ammount = models.FloatField(default=0.0)
    invoice_date = models.DateField()
    bill_start_date = models.DateField()
    bill_end_date = models.DateField()

    class Meta:
        verbose_name = "AWS Account Invoice"
        verbose_name_plural = "AWS Account Invoices"

    def __str__(self):
        return self.aws_account.name + ' - ' + str(self.invoice_date)
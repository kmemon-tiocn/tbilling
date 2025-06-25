# Group model
import uuid
from django.db import models
from modules.customer.models import Customer
from modules.invoice.models import Invoice
from modules.user.basemodel import BaseModel

class Group(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="groups")
    group_name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.group_name

    class Meta:
        unique_together = ['group_name', 'customer']

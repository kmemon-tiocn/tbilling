# Customer model
import uuid
from django.db import models
from modules.partner.models import Partner
from modules.user.basemodel import BaseModel

class Customer(BaseModel):
    provider_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    business_id = models.CharField(max_length=100, unique=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="customers")

    def __str__(self):
        return self.customer_name

    class Meta:
        unique_together = ['customer_name', 'partner']

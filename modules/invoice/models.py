# Invoice model
import uuid
from django.db import models
from modules.user.basemodel import BaseModel

class Invoice(BaseModel):
    invoice_number = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()

    def __str__(self):
        return self.invoice_number

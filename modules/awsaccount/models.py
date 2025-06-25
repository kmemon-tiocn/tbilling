# AwsAccount model (with invitation status)
import uuid
from django.db import models
from modules.group.models import Group
from modules.partner.models import Partner
from modules.customer.models import Customer
from modules.user.basemodel import BaseModel

class AwsAccount(BaseModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="aws_accounts")
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="aws_accounts")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="aws_accounts")
    aws_mail = models.EmailField()
    invitation = models.BooleanField(default=False)
    invitation_status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )

    def __str__(self):
        return f"AWS Account - {self.aws_mail}"

    class Meta:
        unique_together = ['aws_mail', 'customer', 'partner']

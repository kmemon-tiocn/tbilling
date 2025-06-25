import uuid
import copy
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.forms.models import model_to_dict

# Base Model with common fields
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    update_history = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Code for tracking updates and changes
        if self.pk:
            try:
                old_instance = type(self).objects.get(pk=self.pk)
            except type(self).DoesNotExist:
                old_instance = None

            if old_instance:
                old_data = model_to_dict(old_instance)
                new_data = model_to_dict(self)

                update_record = []
                for field, old_value in old_data.items():
                    if 'update_history' in field:
                        continue
                    new_value = new_data.get(field)
                    if old_value != new_value:
                        update_record.append({
                            'note': f'Field "{field}" updated from "{old_value}" to "{new_value}"',
                            'field': field,
                            'updated_by': str(self.updated_by),
                            'updated_at': self.updated_at.isoformat(),
                        })

                if update_record:
                    if self.update_history is None:
                        self.update_history = []
                    self.update_history.extend(copy.deepcopy(update_record))

        super().save(*args, **kwargs)


# User model (inherits from BaseModel)
class User(BaseModel, AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
    
    # New fields
    type = models.CharField(max_length=50, choices=[
        ('CustomerUser', 'Customer User'),
        ('CustomerManager', 'Customer Manager'),
        ('PartnerManager', 'Partner Manager'),
        ('PartnerUser', 'Partner User')
    ])
    
    # Partner and Customer Information
    partner = models.ForeignKey('Partner', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone_number']

    def set_password(self, password):
        self.password = make_password(password)

    def check_password(self, password):
        return self.password == make_password(password)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['email', 'type']  # Ensuring no duplicate user with the same email and type


# Partner model (with AWS keys)
class Partner(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    logo = models.ImageField(upload_to='partners/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    contact_number = models.CharField(max_length=20)

    # New AWS Keys
    aws_access_key_id = models.CharField(max_length=255, null=True, blank=True)
    aws_secret_access_key = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


# Customer model
class Customer(BaseModel):
    provider_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    business_id = models.CharField(max_length=100, unique=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="customers")

    def __str__(self):
        return self.customer_name

    class Meta:
        unique_together = ['customer_name', 'partner']  # Ensuring that a customer with the same name cannot be repeated under the same partner


# AwsAccount model (with invitation status)
class AwsAccount(BaseModel):
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name="aws_accounts")
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="aws_accounts")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="aws_accounts")
    aws_mail = models.EmailField()  # AWS-related email

    # New fields for invitation and status
    invitation = models.BooleanField(default=False)  # Whether the AWS account is invited
    invitation_status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )

    def __str__(self):
        return f"AWS Account - {self.aws_mail}"

    class Meta:
        unique_together = ['aws_mail', 'customer', 'partner']  # Ensuring unique AWS account by email, customer, and partner


# Group model
class Group(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="groups")
    group_name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.group_name

    class Meta:
        unique_together = ['group_name', 'customer']  # Ensuring unique group name per customer


# Invoice model (just a placeholder for relationship reference)
class Invoice(BaseModel):
    invoice_number = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()

    def __str__(self):
        return self.invoice_number

import uuid
import copy
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password
from django.forms.models import model_to_dict

# Base Model with common fields
class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class UserManager(BaseUserManager):
    def _create_user(self, name, email, phone_number, password, **extra_fields):
        if not name:
            raise ValueError('The given name must be set')
        if not email:
            raise ValueError('The given email must be set')
        if not phone_number:
            raise ValueError('The given phone number must be set')
        user = self.model(name=name, email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, name, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)  # Ensure normal users are active by default
        return self._create_user(name, email, phone_number, password, **extra_fields)

    def create_superuser(self, name, email, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  # Ensure superusers are always active

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(name, email, phone_number, password, **extra_fields)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    password = models.CharField(max_length=255)

    type = models.CharField(max_length=50, choices=[ 
        ('CustomerUser', 'Customer User'),
        ('CustomerManager', 'Customer Manager'),
        ('PartnerManager', 'Partner Manager'),
        ('PartnerUser', 'Partner User')
    ])

    partner = models.ForeignKey('Partner', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True)
    is_staff = models.BooleanField(default=False) 
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone_number']
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.name


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



class Customer(BaseModel):
    provider_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    business_id = models.CharField(max_length=100, unique=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="customers")

    def __str__(self):
        return self.customer_name

    class Meta:
        unique_together = ['customer_name', 'partner']

REQUEST_STATUS_CHOICES = (
    ('REQUESTED', 'Requested'),
    ('OPEN', 'Open'),
    ('CANCELED', 'Canceled'),
    ('ACCEPTED', 'Accepted'),
    ('DECLINED', 'Declined'),
    ('EXPIRED', 'Expired'),
)

class AwsAccount(BaseModel):
    account_id = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="aws_accounts")
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    invitation_status = models.CharField(max_length=30, choices=REQUEST_STATUS_CHOICES, default='REQUESTED')
    invitation_id = models.CharField(max_length=50, null=True, blank=True)
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name="aws_accounts")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"AWS Account - {self.email}"


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

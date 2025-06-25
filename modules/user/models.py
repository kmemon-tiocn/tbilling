# User model (inherits from BaseModel)
import uuid
import copy
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.forms.models import model_to_dict
from modules.partner.models import Partner
from modules.customer.models import Customer
from modules.user.basemodel import BaseModel

class User(BaseModel, AbstractBaseUser):
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
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
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
        unique_together = ['email', 'type']

# Partner model (with AWS keys)
import uuid
from django.db import models
from modules.user.basemodel import BaseModel

class Partner(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    logo = models.ImageField(upload_to='partners/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    contact_number = models.CharField(max_length=20)
    aws_access_key_id = models.CharField(max_length=255, null=True, blank=True)
    aws_secret_access_key = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

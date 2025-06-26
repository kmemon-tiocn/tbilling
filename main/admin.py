from django.contrib import admin
from .models import UserManager, User, Partner, Customer, AwsAccount

# Register your models here.
admin.site.register(User)
admin.site.register(Partner)
admin.site.register(Customer)
admin.site.register(AwsAccount)


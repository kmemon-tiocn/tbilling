from django.contrib import admin
from main.models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Partner)
admin.site.register(Customer)
admin.site.register(AwsAccount)
admin.site.register(Group)
admin.site.register(RootInvoice)
admin.site.register(AWSAccountInvoice)
admin.site.register(Service)
admin.site.register(AccountService)
admin.site.register(AwsCostManagement)
admin.site.register(MonthlyCostByAccount)
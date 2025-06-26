from .views import *
from django.urls import path

urlpatterns = [
    path('get-invoice/', GetInvoiceAPIView.as_view(), name='get-organization-invoice'),
    path('sync-cost-management/', SyncCostManagementAPIView.as_view(), name='sync-cost-management'),
]
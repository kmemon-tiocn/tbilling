from django.urls import path
from .views.login import LoginView, LogoutView
from .views.dashboard import dashboard_view
from .views.forgot_password import ForgotPasswordView
from .views.password_reset_confirm import PasswordResetConfirmView
from django.views.generic import TemplateView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', TemplateView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

## Temporary Code
from .views.dashboard import project_table, client_list

urlpatterns += [
    path('project-table/', project_table, name='project-table'),
    path('client-list/', client_list, name='client-list'),
]

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')





##Temporary Code 

@login_required
def project_table(request):
    return render(request, 'project-table.html')

@login_required
def client_list(request):
    return render(request, 'client-table.html')
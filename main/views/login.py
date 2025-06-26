from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views import View

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')  # Redirect to dashboard
        return render(request, 'auth-login.html')

    def post(self, request):
        email = request.POST.get('emailaddress')
        password = request.POST.get('password')
        context = {}
        try:
            if not email or not password:
                context['modal_error'] = 'Email and password are required.'
                return render(request, 'auth-login.html', context)
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('dashboard')  # Redirect to dashboard
                else:
                    context['modal_error'] = 'Your account is inactive. Please contact admin.'
            else:
                context['modal_error'] = 'Invalid email or password.'
        except Exception as e:
            context['modal_error'] = 'An error occurred during login. Please try again.'
        return render(request, 'auth-login.html', context)

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('login')

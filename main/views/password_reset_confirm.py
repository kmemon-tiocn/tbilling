from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.views import View

User = get_user_model()

class PasswordResetConfirmView(View):
    def get(self, request, uidb64, token):
        context = {'validlink': False}
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            context['validlink'] = True
            context['uidb64'] = uidb64
            context['token'] = token
        return render(request, 'password_reset_confirm.html', context)

    def post(self, request, uidb64, token):
        context = {'validlink': False}
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')
            if password1 and password2 and password1 == password2:
                user.set_password(password1)
                user.save()
                return redirect('password_reset_complete')
            else:
                context['validlink'] = True
                context['uidb64'] = uidb64
                context['token'] = token
                context['error'] = 'Passwords do not match or are empty.'
        return render(request, 'password_reset_confirm.html', context)

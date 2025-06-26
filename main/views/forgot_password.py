from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.views import View

User = get_user_model()

class ForgotPasswordView(View):
    def get(self, request):
        return render(request, 'forgot-password.html')

    def post(self, request):
        email = request.POST.get('email')
        context = {}
        if not email:
            context['error'] = 'Please enter your email address.'
            return render(request, 'forgot-password.html', context)
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            subject = 'Password Reset Requested'
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'uid': uid,
                'token': token,
                'protocol': protocol,
                'domain': domain,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            return render(request, 'password_reset_done.html')
        except User.DoesNotExist:
            context['error'] = 'No user found with this email address.'
        except Exception:
            context['error'] = 'There was an error sending the reset email. Please try again.'
        return render(request, 'forgot-password.html', context)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from main.models.core import User

@receiver(post_save, sender=User)
def send_partner_manager_credentials(sender, instance, created, **kwargs):
    if created and instance.type == 'PartnerManager':
        # If password is not set, generate one
        if not instance.password or instance.password == '':
            password = get_random_string(10)
            instance.set_password(password)
            instance.save(update_fields=['password'])
        else:
            password = None  # Password was already set

        # Send email with credentials
        subject = 'Your Partner Manager Account Credentials'
        message = f"Hello {instance.name},\n\nYour Partner Manager account has been created.\n"
        message += f"Email: {instance.email}\n"
        if password:
            message += f"Password: {password}\n"
        else:
            message += "Please use the password you set during registration.\n"
        message += "\nYou can now log in to the admin panel.\n"

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )

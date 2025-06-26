from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, BadHeaderError
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
        # Do not send the password in the email

        # Send email with credentials
        subject = 'Your Partner Manager Account Credentials'
        message = f"""
                    Hello {instance.name},

                    Your Partner Manager account has been created.

                    Email: {instance.email}
                    Password: {instance.password if instance.password else 'A password has been generated for you.'}
                    Please use the password you set during registration.

                    You can now log in to the admin panel.
                """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
                fail_silently=False,
            )
        except BadHeaderError:
            # Optionally log this error
            pass

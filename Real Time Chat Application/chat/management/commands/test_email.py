from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Tests the Django email configuration by sending a test email to the specified address'

    def add_arguments(self, parser):
        parser.add_argument('to_email', type=str, help='Target email address to receive the test email')

    def handle(self, *args, **options):
        to_email = options['to_email'].strip()
        self.stdout.write(self.style.NOTICE(f"Current EMAIL_BACKEND: {settings.EMAIL_BACKEND}"))
        self.stdout.write(self.style.NOTICE(f"Current EMAIL_HOST: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}"))
        self.stdout.write(self.style.NOTICE(f"Current EMAIL_HOST_USER: {settings.EMAIL_HOST_USER or '(Not set - using console mode)'}"))
        self.stdout.write(self.style.NOTICE(f"Attempting to send test email to: {to_email}...\n"))

        try:
            send_mail(
                subject='[DjangoChat] Test Notification Email',
                message='Success! Your DjangoChat email notification service is properly configured and working.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"\n[SUCCESS] Test email successfully dispatched to {to_email}!"))
            if 'smtp' in settings.EMAIL_BACKEND.lower():
                self.stdout.write(self.style.SUCCESS("Check your Gmail inbox (and Spam folder) now."))
            else:
                self.stdout.write(self.style.WARNING("Note: Server is currently in Console mode, so the email was printed above rather than sent over the internet."))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"\n[ERROR] Failed to send email: {exc}"))
            self.stdout.write(self.style.NOTICE(
                "\nTroubleshooting tips for Gmail:\n"
                "1. Did you generate a 16-character Google App Password (not your regular login password)?\n"
                "2. Is 2-Step Verification enabled on your Google Account?\n"
                "3. Ensure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set correctly in DjangoChat/settings.py."
            ))


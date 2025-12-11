from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

@shared_task
def send_email_task(subject, to_email, text_body, html_body=None, from_email=None):
    mail = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email or settings.EMAIL_HOST_USER,
        to=[to_email]
    )
    if html_body:
        mail.attach_alternative(html_body, "text/html")

    mail.send()

"""
Celery tasks for asynchronous email operations.

Handles background email sending with support for HTML content,
PDF attachments, and customizable email parameters for the HRMS system.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(
    subject, to_email, text_body, pdf_bytes, filename, html_body=None, from_email=None
):
    """Send email asynchronously with optional HTML content and PDF attachment.

    Handles email sending in background to avoid blocking API responses.
    Supports both plain text and HTML emails with optional PDF attachments
    for payslips, reports, and notifications.

    Args:
        subject (str): Email subject line
        to_email (str): Recipient email address
        text_body (str): Plain text email content
        pdf_bytes (bytes): PDF file content for attachment
        filename (str): Name for PDF attachment
        html_body (str, optional): HTML email content
        from_email (str, optional): Sender email address
    """
    mail = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email or settings.EMAIL_HOST_USER,
        to=[to_email],
    )
    if filename and pdf_bytes:
        mail.attach(
            filename=filename,
            content=pdf_bytes,
            mimetype="application/pdf",
        )

    if html_body:
        mail.attach_alternative(html_body, "text/html")

    try:
        sent = mail.send(fail_silently=False)
    except Exception as exc:
        logger.exception("send_email_task failed to=%s subject=%s", to_email, subject)
        if settings.DEBUG:
            return 0
        raise exc from exc
    return sent

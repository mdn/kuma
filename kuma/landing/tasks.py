import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import translation
from djcelery_transactions import task as transaction_task

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.email_utils import render_email


log = logging.getLogger('kuma.landing.tasks')


@transaction_task
@skip_in_maintenance_mode
def contribute_thank_you_email(username, user_email):
    """Create a notification email for new contributor."""
    message_context = {
        'user_email': user_email,
        'username': username
    }

    locale = settings.WIKI_DEFAULT_LANGUAGE
    log.debug('Using the locale %s to send the contribution thank you email', locale)

    with translation.override(locale):
        subject = render_email(
            'landing/email/contribution_thank_you_subject.ltxt',
            message_context
        )
        content_plain = render_email(
            'landing/email/contribution_thank_you_message.ltxt',
            message_context
        )
        content_html = render_email(
            'landing/email/contribution_thank_you_message_html.ltxt',
            message_context
        )

        email = EmailMultiAlternatives(
            subject,
            content_plain,
            settings.DEFAULT_FROM_EMAIL,
            [user_email]
        )
        email.attach_alternative(content_html, 'text/html')
        email.send()

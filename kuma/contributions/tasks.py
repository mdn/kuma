import logging

from celery.task import task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import translation

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.email_utils import render_email


log = logging.getLogger('kuma.contributions.tasks')


@task
@skip_in_maintenance_mode
def contribute_thank_you_email(username, user_email):
    """Create a notification email for new contributor."""
    message_context = {
        'user_email': user_email,
        'username': username,
    }

    # TODO: Remove when we ship translations, get legal approval
    locale = settings.WIKI_DEFAULT_LANGUAGE
    log.debug('Using the locale %s to send the contribution thank you email', locale)

    with translation.override(locale):
        subject = render_email(
            'contributions/email/thank_you/subject.ltxt',
            message_context
        )
        content_plain = render_email(
            'contributions/email/thank_you/plain.ltxt',
            message_context
        )
        content_html = render_email(
            'contributions/email/thank_you/email.html',
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

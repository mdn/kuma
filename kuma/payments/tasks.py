from __future__ import unicode_literals

import logging

from celery.task import task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import translation

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.email_utils import render_email
from kuma.core.urlresolvers import reverse
from kuma.wiki.templatetags.jinja_helpers import absolutify


log = logging.getLogger('kuma.payments.tasks')


@task
@skip_in_maintenance_mode
def payments_thank_you_email(username, user_email, recurring=False):
    """Create a notification email for new contributor."""
    message_context = {
        'user_email': user_email,
        'username': username,
        'support_mail_link': 'mailto:' + settings.CONTRIBUTION_SUPPORT_EMAIL + '?Subject=Recurring%20payment%20support',
        'support_mail': settings.CONTRIBUTION_SUPPORT_EMAIL,
        'recurring_payment': recurring,
        'recurring_payment_management': absolutify(reverse('recurring_payment_management')),
    }

    # TODO: Remove when we ship translations, get legal approval
    locale = settings.WIKI_DEFAULT_LANGUAGE
    log.debug('Using the locale %s to send the contribution thank you email', locale)

    with translation.override(locale):
        subject = render_email(
            'payments/email/thank_you/subject.ltxt',
            message_context
        )
        content_plain = render_email(
            'payments/email/thank_you/plain.ltxt',
            message_context
        )
        content_html = render_email(
            'payments/email/thank_you/email.html',
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

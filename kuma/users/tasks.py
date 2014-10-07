import logging
import constance.config
from celery.task import task
from tower import ugettext_lazy as _

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from devmo.utils import strings_are_translated
from devmo.email_utils import uselocale

log = logging.getLogger('mdn.email')


WELCOME_EMAIL_STRINGS = [
    "Like words?",
    "Don't be shy, if you have any doubt, problems, questions: contact us! We are here to help."
]


@task
def send_welcome_email(user_pk, locale):
    user = User.objects.get(pk=user_pk)
    if (locale == settings.WIKI_DEFAULT_LANGUAGE or
            strings_are_translated(WELCOME_EMAIL_STRINGS, locale)):
        context = {'username': user.username}
        log.debug('Using the locale %s to send the welcome email', locale)
        with uselocale(locale):
            content_plain = render_to_string('users/email/welcome/plain.ltxt',
                                             context)
            content_html = render_to_string('users/email/welcome/html.ltxt',
                                            context)

            email = EmailMultiAlternatives(
                _('Take the next step to get involved on MDN!'),
                content_plain,
                constance.config.WELCOME_EMAIL_FROM,
                [user.email],
            )
            email.attach_alternative(content_html, 'text/html')
            email.send()

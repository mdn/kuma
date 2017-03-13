import logging

from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives, send_mail
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from djcelery_transactions import task as transaction_task

from kuma.core.email_utils import render_email
from kuma.core.utils import strings_are_translated
from kuma.core.decorators import skip_in_maintenance_mode


log = logging.getLogger('kuma.users.tasks')


WELCOME_EMAIL_STRINGS = [
    "Like words?",
    "Don't be shy, if you have any doubt, problems, questions: contact us! We are here to help."
]


@transaction_task
@skip_in_maintenance_mode
def send_recovery_email(user_pk, email, locale=None):
    user = get_user_model().objects.get(pk=user_pk)
    locale = locale or settings.WIKI_DEFAULT_LANGUAGE
    url = settings.SITE_URL + user.get_recovery_url()
    context = {'recovery_url': url, 'username': user.username}
    with translation.override(locale):
        subject = render_email('users/email/recovery/subject.ltxt', context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        plain = render_email('users/email/recovery/plain.ltxt', context)
        send_mail(subject, plain, settings.DEFAULT_FROM_EMAIL, [email])


@transaction_task
@skip_in_maintenance_mode
def send_welcome_email(user_pk, locale):
    user = get_user_model().objects.get(pk=user_pk)
    if (locale == settings.WIKI_DEFAULT_LANGUAGE or
            strings_are_translated(WELCOME_EMAIL_STRINGS, locale)):
        context = {'username': user.username}
        log.debug('Using the locale %s to send the welcome email', locale)
        with translation.override(locale):
            content_plain = render_email('users/email/welcome/plain.ltxt',
                                         context)
            content_html = render_email('users/email/welcome/html.ltxt',
                                        context)

            email = EmailMultiAlternatives(
                _('Take the next step to get involved on MDN!'),
                content_plain,
                config.WELCOME_EMAIL_FROM,
                [user.email],
            )
            email.attach_alternative(content_html, 'text/html')
            email.send()

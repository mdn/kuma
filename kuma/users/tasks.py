import datetime
import logging
import os
from urllib.parse import urlparse

import requests
from celery import task
from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import formats, translation
from django.utils.translation import gettext_lazy as _

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.email_utils import render_email
from kuma.core.urlresolvers import reverse
from kuma.core.utils import (
    EmailMultiAlternativesRetrying,
    send_mail_retrying,
    strings_are_translated,
)
from kuma.wiki.templatetags.jinja_helpers import absolutify

from .stripe_utils import retrieve_and_synchronize_subscription_info


log = logging.getLogger("kuma.users.tasks")


WELCOME_EMAIL_STRINGS = [
    "Like words?",
    "Don't be shy, if you have any doubt, problems, questions: contact us! We are here to help.",
]


@task
@skip_in_maintenance_mode
def send_recovery_email(user_pk, email, locale=None):
    user = get_user_model().objects.get(pk=user_pk)
    locale = locale or settings.WIKI_DEFAULT_LANGUAGE
    url = settings.SITE_URL + user.get_recovery_url()
    context = {"recovery_url": url, "username": user.username}
    with translation.override(locale):
        subject = render_email("users/email/recovery/subject.ltxt", context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        plain = render_email("users/email/recovery/plain.ltxt", context)
        send_mail_retrying(subject, plain, settings.DEFAULT_FROM_EMAIL, [email])


@task
@skip_in_maintenance_mode
def send_welcome_email(user_pk, locale):
    user = get_user_model().objects.get(pk=user_pk)
    if locale == settings.WIKI_DEFAULT_LANGUAGE or strings_are_translated(
        WELCOME_EMAIL_STRINGS, locale
    ):
        context = {"username": user.username}
        log.debug("Using the locale %s to send the welcome email", locale)
        with translation.override(locale):
            content_plain = render_email("users/email/welcome/plain.ltxt", context)
            content_html = render_email("users/email/welcome/html.ltxt", context)

            email = EmailMultiAlternativesRetrying(
                _("Getting started with your new MDN account"),
                content_plain,
                config.WELCOME_EMAIL_FROM,
                [user.email],
            )
            email.attach_alternative(content_html, "text/html")
            email.send()


@task
@skip_in_maintenance_mode
def send_payment_received_email(payment_intent, locale):
    user = get_user_model().objects.get(stripe_customer_id=payment_intent.customer)
    subscription_info = retrieve_and_synchronize_subscription_info(user)
    locale = locale or settings.WIKI_DEFAULT_LANGUAGE
    context = {
        "payment_date": formats.date_format(
            datetime.datetime.fromtimestamp(payment_intent.created), "DATE_FORMAT"
        ),
        "next_payment_date": formats.date_format(
            subscription_info["next_payment_at"], "DATE_FORMAT"
        ),
        "invoice_number": payment_intent.id,
        "dollar_amount": settings.CONTRIBUTION_AMOUNT_USD,
        "credit_card_brand": subscription_info["brand"],
        "manage_subscription_url": absolutify(reverse("recurring_payment_management")),
        "faq_url": absolutify(reverse("recurring_payment_subscription")),
        "contact_email": settings.CONTRIBUTION_SUPPORT_EMAIL,
    }
    with translation.override(locale):
        subject = render_email("users/email/payment_received/subject.ltxt", context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        plain = render_email("users/email/payment_received/plain.ltxt", context)
        send_mail_retrying(
            subject,
            plain,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            attachment={
                "name": os.path.basename(urlparse(payment_intent.invoice_pdf).path),
                "bytes": requests.get(payment_intent.invoice_pdf).content,
                "mime": "application/pdf",
            },
        )

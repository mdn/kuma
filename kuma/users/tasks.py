import logging

from celery import task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from pyquery import PyQuery as pq

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.email_utils import render_email
from kuma.core.utils import (
    EmailMultiAlternativesRetrying,
    strings_are_translated,
)

log = logging.getLogger("kuma.users.tasks")


WELCOME_EMAIL_STRINGS = [
    "Like words?",
    "Don't be shy, if you have any doubt, problems, questions: contact us! We are here to help.",
]


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
            content_html = render_email("users/email/welcome/html.ltxt", context)
            doc = pq(content_html)
            urls = []
            for i, link in enumerate(doc("body a[href]").items()):
                link.text(f"{link.text()}[{i + 1}]")
                urls.append((i + 1, link.attr("href")))

            content_plain = doc("body").text().replace("\n", "\n\n")
            if urls:
                content_plain += "\n\n"
                for i, url in urls:
                    content_plain += f"[{i}] {url}\n"

            email = EmailMultiAlternativesRetrying(
                _("Getting started with your new MDN account"),
                content_plain,
                settings.WELCOME_EMAIL_FROM,
                [user.email],
            )
            email.attach_alternative(content_html, "text/html")
            email.send()

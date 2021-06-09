import logging

import pytest
from django.conf import settings
from django.core import mail
from django.test import override_settings
from django.utils.log import AdminEmailHandler

from . import assert_no_cache_header, KumaTestCase
from ..urlresolvers import reverse


@override_settings(
    DEBUG=False,
    DEBUG_PROPAGATE_EXCEPTIONS=False,
    ADMINS=(("admin", "admin@example.com"),),
    ROOT_URLCONF="kuma.core.tests.logging_urls",
)
class LoggingTests(KumaTestCase):
    logger = logging.getLogger("django.security")
    suspicous_path = "/en-US/suspicious/"

    def setUp(self):
        super(LoggingTests, self).setUp()
        self.old_handlers = self.logger.handlers[:]

    def tearDown(self):
        super(LoggingTests, self).tearDown()
        self.logger.handlers = self.old_handlers

    def test_no_mail_handler(self):
        self.logger.handlers = [logging.NullHandler()]
        response = self.client.get(self.suspicous_path)
        assert 400 == response.status_code
        assert 0 == len(mail.outbox)

    def test_mail_handler(self):
        self.logger.handlers = [AdminEmailHandler()]
        response = self.client.get(self.suspicous_path)
        assert 400 == response.status_code
        assert 1 == len(mail.outbox)

        assert "admin@example.com" in mail.outbox[0].to
        assert self.suspicous_path in mail.outbox[0].body


class EventsRedirectTest(KumaTestCase):
    def test_redirect_to_mozilla_org(self):
        url = "/en-US/events"
        response = self.client.get(url)
        assert 302 == response.status_code
        assert "https://community.mozilla.org/events/" == response["Location"]


@pytest.mark.parametrize("http_method", ["get", "put", "delete", "options", "head"])
def test_setting_language_cookie_disallowed_methods(client, http_method):
    url = reverse("set-language-cookie")
    response = getattr(client, http_method)(url, {"language": "bn"})
    assert response.status_code == 405
    assert_no_cache_header(response)


def test_setting_language_cookie_working(client):
    url = reverse("set-language-cookie")
    response = client.post(url, {"language": "ja"})
    assert response.status_code == 204
    assert_no_cache_header(response)

    lang_cookie = response.client.cookies.get(settings.LANGUAGE_COOKIE_NAME)

    # Check language cookie is set
    assert lang_cookie
    assert lang_cookie.value == "ja"
    # Check that the max-age from the cookie is the same as our settings
    assert lang_cookie["max-age"] == settings.LANGUAGE_COOKIE_AGE


def test_not_possible_to_set_non_locale_cookie(client):
    url = reverse("set-language-cookie")
    response = client.post(url, {"language": "foo"})
    assert response.status_code == 204
    assert_no_cache_header(response)
    # No language cookie should be saved as `foo` is not a supported locale
    assert not response.client.cookies.get(settings.LANGUAGE_COOKIE_NAME)

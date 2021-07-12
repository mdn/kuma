import logging

from django.core import mail
from django.test import override_settings
from django.utils.log import AdminEmailHandler

from . import KumaTestCase


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

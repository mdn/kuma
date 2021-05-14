import pytest
from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.utils.encoding import force_bytes
from requests.exceptions import ConnectionError

from kuma.core.utils import (
    EmailMultiAlternativesRetrying,
    order_params,
    requests_retry_session,
    safer_pyquery,
    send_mail_retrying,
)


@pytest.mark.parametrize(
    "original,expected",
    (
        ("https://example.com", "https://example.com"),
        ("http://example.com?foo=bar&foo=", "http://example.com?foo=&foo=bar"),
        ("http://example.com?foo=bar&bar=baz", "http://example.com?bar=baz&foo=bar"),
    ),
)
def test_order_params(original, expected):
    assert order_params(original) == expected


def test_safer_pyquery(mock_requests):
    # Note! the `mock_requests` fixture is just there to make absolutely
    # sure the whole test doesn't ever use requests.get().
    # My not setting up expectations, and if it got used,
    # these tests would raise a `NoMockAddress` exception.

    parsed = safer_pyquery("https://www.peterbe.com")
    assert parsed.outer_html() == "<p>https://www.peterbe.com</p>"

    # Byte strings in should continue to work.
    parsed = safer_pyquery(force_bytes("https://www.peterbe.com"))
    assert parsed.outer_html() == "<p>https://www.peterbe.com</p>"

    # Non-ascii as Unicode
    parsed = safer_pyquery("https://www.peterbe.com/ë")

    parsed = safer_pyquery(
        """<!doctype html>
    <html>
        <body>
            <b>Bold!</b>
        </body>
    </html>
    """
    )
    assert parsed("b").text() == "Bold!"
    parsed = safer_pyquery(
        """
    <html>
        <body>
            <a href="https://www.peterbe.com">URL</a>
        </body>
    </html>
    """
    )
    assert parsed("a[href]").text() == "URL"


def test_requests_retry_session(mock_requests):
    def absolute_url(uri):
        return "http://example.com" + uri

    mock_requests.get(absolute_url("/a/ok"), text="hi")
    mock_requests.get(absolute_url("/oh/noes"), text="bad!", status_code=504)
    mock_requests.get(absolute_url("/oh/crap"), exc=ConnectionError)

    session = requests_retry_session(status_forcelist=(504,))
    response_ok = session.get(absolute_url("/a/ok"))
    assert response_ok.status_code == 200

    response_bad = session.get(absolute_url("/oh/noes"))
    assert response_bad.status_code == 504

    with pytest.raises(ConnectionError):
        session.get(absolute_url("/oh/crap"))


class SomeException(Exception):
    """Just a custom exception class."""


class SMTPFlakyEmailBackend(EmailBackend):
    """doc string"""

    def send_messages(self, messages):
        self._attempts = getattr(self, "_attempts", 0) + 1
        if self._attempts < 2:
            raise SomeException("Oh noes!")
        return super(SMTPFlakyEmailBackend, self).send_messages(messages)


def test_send_mail_retrying(settings):
    settings.EMAIL_BACKEND = "kuma.core.tests.test_utils.SMTPFlakyEmailBackend"

    send_mail_retrying(
        "Subject",
        "Message",
        "from@example.com",
        ["to@example.com"],
        retry_options={
            "retry_exceptions": (SomeException,),
            # Overriding defaults to avoid the test being slow.
            "sleeptime": 0.02,
            "jitter": 0.01,
        },
    )
    sent = mail.outbox[-1]
    # sanity check
    assert sent.subject == "Subject"


def test_EmailMultiAlternativesRetrying(settings):
    settings.EMAIL_BACKEND = "kuma.core.tests.test_utils.SMTPFlakyEmailBackend"

    email = EmailMultiAlternativesRetrying(
        "Multi Subject",
        "Content",
        "from@example.com",
        ["to@example.com"],
    )
    email.attach_alternative("<p>Content</p>", "text/html")
    email.send(
        retry_options={
            "retry_exceptions": (SomeException,),
            # Overriding defaults to avoid the test being slow.
            "sleeptime": 0.02,
            "jitter": 0.01,
        }
    )
    sent = mail.outbox[-1]
    # sanity check
    assert sent.subject == "Multi Subject"

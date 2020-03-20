import pytest
from django.utils.encoding import force_bytes
from requests.exceptions import ConnectionError

from kuma.core.utils import (
    order_params,
    requests_retry_session,
    safer_pyquery,
    smart_int,
)


def test_smart_int():
    # Sanity check
    assert 10 == smart_int("10")
    assert 10 == smart_int("10.5")

    # Test int
    assert 10 == smart_int(10)

    # Invalid string
    assert 0 == smart_int("invalid")

    # Empty string
    assert 0 == smart_int("")

    # Wrong type
    assert 0 == smart_int(None)
    assert 10 == smart_int([], 10)


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

    # Note! Since this file uses `__future__.unicode_literals` the only
    # way to produce a byte string is to use force_bytes.
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

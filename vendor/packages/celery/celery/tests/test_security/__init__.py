"""
Keys and certificates for tests (KEY1 is a private key of CERT1, etc.)

Generated with::

    $ openssl genrsa -des3 -passout pass:test -out key1.key 1024
    $ openssl req -new -key key1.key -out key1.csr -passin pass:test
    $ cp key1.key key1.key.org
    $ openssl rsa -in key1.key.org -out key1.key -passin pass:test
    $ openssl x509 -req -days 365 -in cert1.csr \
              -signkey key1.key -out cert1.crt
    $ rm key1.key.org cert1.csr

"""
from __future__ import absolute_import

import __builtin__

from celery import current_app
from celery.exceptions import ImproperlyConfigured
from celery.security import setup_security, disable_untrusted_serializers
from kombu.serialization import registry

from .case import SecurityCase


KEY1 = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDCsmLC+eqL4z6bhtv0nzbcnNXuQrZUoh827jGfDI3kxNZ2LbEy
kJOn7GIl2tPpcY2Dm1sOM8G1XLm/8Izprp4ifpF4Gi0mqz0GquY5dcMNASG9zkRO
J1z8dQUyp3PIUHdQdrKbYQVifkA4dh6Kg27k8/IcdY1lHsaIju4bX7MADwIDAQAB
AoGBAKWpCRWjdiluwu+skO0Up6aRIAop42AhzfN8OuZ81SMJRP2rJTHECI8COATD
rDneb63Ce3ibG0BI1Jf3gr624D806xVqK/SVHZNbfWx0daE3Q43DDk1UdhRF5+0X
HPqqU/IdeW1YGyWJi+IhMTXyGqhZ1BTN+4vHL7NlRpDt6JOpAkEA+xvfRO4Ca7Lw
NEgvW7n+/L9b+xygQBtOA5s260pO+8jMrXvOdCjISaKHD8HZGFN9oUmLsDXXBhjh
j0WCMdsHbQJBAMZ9OIw6M/Uxv5ANPCD58p6PZTb0knXVPMYBFQ7Y/h2HZzqbEyiI
DLGZpAa9/IhVkoCULd/TNytz5rl27KEni+sCQArFQEdZmhr6etkTO4zIpoo6vvw/
VxRI14jKEIn5Dvg3vae3RryuvyCBax+e5evoMNxJJkexl354dLxLc/ElfuUCQQCq
U14pBvD7ITuPM6w7aAEIi2iBZhIgR2GlT9xwJ0i4si6lHdms2EJ8TKlyl6mSnEvh
RkavYSJgiU6eLC0WhUcNAkEA7vuNcz/uuckmq870qfSzUQJIYLzwVOadEdEEAVy0
L0usztlKmAH8U/ceQMMJLMI9W4m680JrMf3iS7f+SkgUTA==
-----END RSA PRIVATE KEY-----"""

KEY2 = """-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDH22L8b9AmST9ABDmQTQ2DWMdDmK5YXZt4AIY81IcsTQ/ccM0C
fwXEP9tdkYwtcxMCWdASwY5pfMy9vFp0hyrRQMSNfuoxAgONuNWPyQoIvY3ZXRe6
rS+hb/LN4+vdjX+oxmYiQ2HmSB9rh2bepE6Cw+RLJr5sXXq+xZJ+BLt5tQIDAQAB
AoGBAMGBO0Arip/nP6Rd8tYypKjN5nEefX/1cjgoWdC//fj4zCil1vlZv12abm0U
JWNEDd2y0/G1Eow0V5BFtFcrIFowU44LZEiSf7sKXlNHRHlbZmDgNXFZOt7nVbHn
6SN+oCYjaPjji8idYeb3VQXPtqMoMn73MuyxD3k3tWmVLonpAkEA6hsu62qhUk5k
Nt88UZOauU1YizxsWvT0bHioaceE4TEsbO3NZs7dmdJIcRFcU787lANaaIq7Rw26
qcumME9XhwJBANqMOzsYQ6BX54UzS6x99Jjlq9MEbTCbAEZr/yjopb9f617SwfuE
AEKnIq3HL6/Tnhv3V8Zy3wYHgDoGNeTVe+MCQQDi/nyeNAQ8RFqTgh2Ak/jAmCi0
yV/fSgj+bHgQKS/FEuMas/IoL4lbrzQivkyhv5lLSX0ORQaWPM+z+A0qZqRdAkBh
XE+Wx/x4ljCh+nQf6AzrgIXHgBVUrfi1Zq9Jfjs4wnaMy793WRr0lpiwaigoYFHz
i4Ei+1G30eeh8dpYk3KZAkB0ucTOsQynDlL5rLGYZ+IcfSfH3w2l5EszY47kKQG9
Fxeq/HOp9JYw4gRu6Ycvqu57KHwpHhR0FCXRBxuYcJ5V
-----END RSA PRIVATE KEY-----"""

CERT1 = """-----BEGIN CERTIFICATE-----
MIICATCCAWoCCQCR6B3XQcBOvjANBgkqhkiG9w0BAQUFADBFMQswCQYDVQQGEwJB
VTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50ZXJuZXQgV2lkZ2l0
cyBQdHkgTHRkMB4XDTExMDcxOTA5MDgyMloXDTEyMDcxODA5MDgyMlowRTELMAkG
A1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoMGEludGVybmV0
IFdpZGdpdHMgUHR5IEx0ZDCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAwrJi
wvnqi+M+m4bb9J823JzV7kK2VKIfNu4xnwyN5MTWdi2xMpCTp+xiJdrT6XGNg5tb
DjPBtVy5v/CM6a6eIn6ReBotJqs9BqrmOXXDDQEhvc5ETidc/HUFMqdzyFB3UHay
m2EFYn5AOHYeioNu5PPyHHWNZR7GiI7uG1+zAA8CAwEAATANBgkqhkiG9w0BAQUF
AAOBgQA4+OiJ+pyq9lbEMFYC9K2+e77noHJkwUOs4wO6p1R14ZqSmoIszQ7KEBiH
2HHPMUY6kt4GL1aX4Vr1pUlXXdH5WaEk0fvDYZemILDMqIQJ9ettx8KihZjFGC4k
Y4Sy5xmqdE9Kjjd854gTRRnzpMnJp6+74Ki2X8GHxn3YBM+9Ng==
-----END CERTIFICATE-----"""

CERT2 = """-----BEGIN CERTIFICATE-----
MIICATCCAWoCCQCV/9A2ZBM37TANBgkqhkiG9w0BAQUFADBFMQswCQYDVQQGEwJB
VTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50ZXJuZXQgV2lkZ2l0
cyBQdHkgTHRkMB4XDTExMDcxOTA5MDkwMloXDTEyMDcxODA5MDkwMlowRTELMAkG
A1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoMGEludGVybmV0
IFdpZGdpdHMgUHR5IEx0ZDCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAx9ti
/G/QJkk/QAQ5kE0Ng1jHQ5iuWF2beACGPNSHLE0P3HDNAn8FxD/bXZGMLXMTAlnQ
EsGOaXzMvbxadIcq0UDEjX7qMQIDjbjVj8kKCL2N2V0Xuq0voW/yzePr3Y1/qMZm
IkNh5kgfa4dm3qROgsPkSya+bF16vsWSfgS7ebUCAwEAATANBgkqhkiG9w0BAQUF
AAOBgQBzaZ5vBkzksPhnWb2oobuy6Ne/LMEtdQ//qeVY4sKl2tOJUCSdWRen9fqP
e+zYdEdkFCd8rp568Eiwkq/553uy4rlE927/AEqs/+KGYmAtibk/9vmi+/+iZXyS
WWZybzzDZFncq1/N1C3Y/hrCBNDFO4TsnTLAhWtZ4c0vDAiacw==
-----END CERTIFICATE-----"""


class TestSecurity(SecurityCase):

    def tearDown(self):
        registry._disabled_content_types.clear()

    def test_disable_untrusted_serializers(self):
        disabled = registry._disabled_content_types
        self.assertEqual(0, len(disabled))

        disable_untrusted_serializers(
                ['application/json', 'application/x-python-serialize'])
        self.assertIn('application/x-yaml', disabled)
        self.assertNotIn('application/json', disabled)
        self.assertNotIn('application/x-python-serialize', disabled)
        disabled.clear()

        disable_untrusted_serializers()
        self.assertIn('application/x-yaml', disabled)
        self.assertIn('application/json', disabled)
        self.assertIn('application/x-python-serialize', disabled)

    def test_setup_security(self):
        disabled = registry._disabled_content_types
        self.assertEqual(0, len(disabled))

        current_app.conf.CELERY_TASK_SERIALIZER = 'json'

        setup_security()
        self.assertIn('application/x-python-serialize', disabled)
        disabled.clear()

    def test_security_conf(self):
        current_app.conf.CELERY_TASK_SERIALIZER = 'auth'

        self.assertRaises(ImproperlyConfigured, setup_security)

        _import = __builtin__.__import__

        def import_hook(name, *args, **kwargs):
            if name == 'OpenSSL':
                raise ImportError
            return _import(name, *args, **kwargs)

        __builtin__.__import__ = import_hook
        self.assertRaises(ImproperlyConfigured, setup_security)
        __builtin__.__import__ = _import

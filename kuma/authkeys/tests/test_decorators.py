import base64

import pytest

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.http import HttpRequest

from kuma.core.tests import eq_, ok_
from kuma.users.tests import user

from ..models import Key
from ..decorators import accepts_auth_key


class KeyDecoratorsTest(TestCase):

    @pytest.mark.current
    def test_key_auth_decorator(self):

        u = user(username="test23", email="test23@example.com", save=True)

        key = Key(user=u)
        secret = key.generate_secret()
        key.save()

        @accepts_auth_key
        def fake_view(request, foo, bar):
            return (foo, bar)

        cases = ((key.key, secret, True),
                 (key.key, 'FAKE', False),
                 ('FAKE', secret, False),
                 ('FAKE', 'FAKE', False))

        for k, s, success in cases:

            request = HttpRequest()
            request.user = AnonymousUser()

            auth = '%s:%s' % (k, s)
            b64_auth = base64.encodestring(auth)
            request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % b64_auth

            foo, bar = fake_view(request, 'foo', 'bar')
            eq_('foo', foo)
            eq_('bar', bar)

            if not success:
                ok_(not request.user.is_authenticated())
            else:
                ok_(request.user.is_authenticated())
                ok_(request.user == u)
                ok_(request.authkey)
                ok_(request.authkey == key)

        # Test with incorrect auth header
        request = HttpRequest()
        request.user = AnonymousUser()
        request.META['HTTP_AUTHORIZATION'] = "Basic bad_auth_string"

        # Make a request to the view
        fake_view(request, 'foo', 'bar')

        # The user should not be authonticated and no server error should raise
        ok_(not request.user.is_authenticated())

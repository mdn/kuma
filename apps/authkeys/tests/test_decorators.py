# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import time
import base64

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.test.client import Client
from django.http import HttpRequest

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from authkeys.models import Key
from authkeys.decorators import accepts_auth_key


class KeyDecoratorsTest(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @attr('current')
    def test_key_auth_decorator(self):

        user = User(username="test23", email="test23@example.com")
        user.save()

        key = Key(user=user)
        secret = key.generate_secret()
        key.save()

        @accepts_auth_key
        def fake_view(request, foo, bar):
            return (foo, bar)

        cases = ((key.key, secret, True),
                 (key.key, 'FAKE', False),
                 ('FAKE',  secret, False),
                 ('FAKE',  'FAKE', False))

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
                ok_(request.user == user)
                ok_(request.authkey)
                ok_(request.authkey == key)

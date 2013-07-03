# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import time

from django.conf import settings
from django.db import connection

from django.contrib.auth.models import AnonymousUser, User

from django.test import TestCase
from django.test.client import Client

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.db import models

from authkeys.models import Key


class KeyViewsTest(TestCase):

    def setUp(self):
        self.user = User(username="tester23",
                         email="tester23@example.com")
        self.user.save()

    def tearDown(self):
        self.user.delete()

    @attr('current')
    def test_secret_generation(self):
        """Generated secret should be saved as a hash and pass a check"""
        key = Key(user=self.user)
        secret = key.generate_secret()
        key.save()
        ok_(key.key)
        ok_(key.hashed_secret)
        ok_(len(key.hashed_secret) > 0)
        ok_(len(secret) > 0)
        ok_(secret != key.hashed_secret)
        ok_(not key.check_secret("I AM A FAKE"))
        ok_(key.check_secret(secret))

import logging
import time

from django.conf import settings
from django.db import connection

from django.contrib.auth.models import AnonymousUser

from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.db import models

from .models import TestModel
from .fields import ActionCounterField


class ActionCountersTest(TestCase):

    def setUp(self):
        settings.DEBUG = True

        self.user1 = User.objects.create_user(
            'tester1', 'tester2@tester.com', 'tester1')
        self.user1.save()

        self.user2 = User.objects.create_user(
            'tester2', 'tester2@tester.com', 'tester2')
        self.user2.save()

        self.obj_1 = TestModel(title="alpha")
        self.obj_1.save()

    def tearDown(self):
        #for sql in connection.queries:
        #    logging.debug("SQL %s" % sql)
        pass

    def mk_request(self, user=None, session_key=None, ip='192.168.123.123', 
            user_agent='FakeBrowser 1.0'):
        request = HttpRequest()
        request.user = user and user or AnonymousUser()
        if session_key:
            request.session = Session()
            request.session.session_key = session_key
        request.method = 'GET'
        request.META['REMOTE_ADDR'] = ip
        request.META['HTTP_USER_AGENT'] = user_agent
        return request

    def test_basic_action_increment(self):
        """Action attempted with several different kinds of unique identifiers"""

        obj_1 = self.obj_1

        # set up request for anonymous user #1
        request = self.mk_request()

        # anonymous user #1 likes user2
        obj_1.likes.increment(request)
        eq_(1, obj_1.likes.total)

        # anonymous user #1 likes user2, again
        obj_1.likes.increment(request)
        eq_(1, obj_1.likes.total)

        # set up request for anonymous user #2
        request = self.mk_request(ip='192.168.123.1')

        # anonymous user #2 likes user2
        obj_1.likes.increment(request)
        eq_(2, obj_1.likes.total)

        # anonymous user #2 likes user2, again
        obj_1.likes.increment(request)
        eq_(2, obj_1.likes.total)

        # set up request for authenticated user1
        request = self.mk_request(user=self.user1)

        # authenticated user1 likes user2
        obj_1.likes.increment(request)
        eq_(3, obj_1.likes.total)

        # authenticated user1 likes user2, again
        obj_1.likes.increment(request)
        eq_(3, obj_1.likes.total)

        # authenticated user1 likes user2, again, from another IP
        request.META['REMOTE_ADDR'] = '192.168.123.50'
        obj_1.likes.increment(request)
        eq_(3, obj_1.likes.total)

        # set up request for user agent Mozilla 1.0
        request = self.mk_request(ip='192.168.123.50', user_agent='Mozilla 1.0')
        obj_1.likes.increment(request)
        eq_(4, obj_1.likes.total)

        # set up request for user agent Safari 1.0
        request = self.mk_request(ip='192.168.123.50', user_agent='Safari 1.0')
        obj_1.likes.increment(request)
        eq_(5, obj_1.likes.total)

    def test_action_with_max(self):
        """Action with a max_total_per_unique greater than 1"""
        obj_1 = self.obj_1
        MAX = obj_1.views.field.max_total_per_unique

        request = self.mk_request(ip='192.168.123.123')
        for x in range(1, MAX+1):
            obj_1.views.increment(request)
            eq_(x, obj_1.views.total)

        obj_1.views.increment(request)
        eq_(MAX, obj_1.views.total)

        obj_1.views.increment(request)
        eq_(MAX, obj_1.views.total)

    def test_action_with_min(self):
        """Action with a min_total_per_unique greater than 1"""
        obj_1 = self.obj_1
        MIN = obj_1.frobs.field.min_total_per_unique

        request = self.mk_request(ip='192.168.123.123')
        for x in range(1, (0-MIN)+1):
            obj_1.frobs.decrement(request)
            eq_(0-x, obj_1.frobs.total)

        obj_1.frobs.decrement(request)
        eq_(MIN, obj_1.frobs.total)

        obj_1.frobs.decrement(request)
        eq_(MIN, obj_1.frobs.total)

    def test_action_count_per_unique(self):
        """Exercise action counts per unique and ensure overall total works"""
        obj_1 = self.obj_1

        MAX = obj_1.boogs.field.max_total_per_unique
        MIN = obj_1.boogs.field.min_total_per_unique

        UNIQUES = ( 
            dict(user=self.user1),
            dict(user=self.user2),
            dict(ip='192.168.123.123'), 
            dict(ip='192.168.123.150', user_agent="Safari 1.0"), 
            dict(ip='192.168.123.150', user_agent="Mozilla 1.0"), 
            dict(ip='192.168.123.160'), 
        )

        for unique in UNIQUES:
            request = self.mk_request(**unique)

            for x in range(1, MAX+1):
                obj_1.boogs.increment(request)
                eq_(x, obj_1.boogs.get_total_for_request(request))

            obj_1.boogs.increment(request)
            obj_1.boogs.increment(request)
            eq_(MAX, obj_1.boogs.get_total_for_request(request))

        eq_(MAX * len(UNIQUES), obj_1.boogs.total)

        # Undo all the increments before going below zero
        for unique in UNIQUES:
            request = self.mk_request(**unique)
            for x in range(1, MAX+1):
                obj_1.boogs.decrement(request)

        for unique in UNIQUES:
            request = self.mk_request(**unique)

            for x in range(1, (0-MIN)+1):
                obj_1.boogs.decrement(request)
                eq_(0-x, obj_1.boogs.get_total_for_request(request))

            obj_1.boogs.decrement(request)
            obj_1.boogs.decrement(request)
            eq_(MIN, obj_1.boogs.get_total_for_request(request))

        eq_(MIN * len(UNIQUES), obj_1.boogs.total)

    def test_count_starts_at_zero(self):
        """Make sure initial count is zero.

        Sounds dumb, but it was a bug at one point."""
        request = self.mk_request()
        eq_(0, self.obj_1.likes.get_total_for_request(request))


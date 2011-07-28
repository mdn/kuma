import logging
import time

from django.conf import settings
from django.db import connection

from django.core.exceptions import MultipleObjectsReturned

from django.contrib.auth.models import AnonymousUser

from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from .models import ContentFlag
from .utils import get_ip, get_unique

class DemoPackageTest(TestCase):

    def setUp(self):
        settings.DEBUG = True

        self.user1 = User.objects.create_user('tester1', 
                'tester2@tester.com', 'tester1')
        self.user1.save()

        self.user2 = User.objects.create_user('tester2', 
                'tester2@tester.com', 'tester2')
        self.user2.save()

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

    def test_bad_multiple_flags(self):
        """Force multiple flags, possibly result of race condition, ensure graceful handling"""
        request = self.mk_request()
        user, ip, user_agent, session_key = get_unique(request)

        obj_1 = self.user2
        obj_1_ct = ContentType.objects.get_for_model(obj_1)

        f1 = ContentFlag(content_type=obj_1_ct, object_pk=obj_1.pk,
                flag_type="Broken thing",
                ip=ip, user_agent=user_agent, user=user, session_key=session_key)
        f1.save()

        f2 = ContentFlag(content_type=obj_1_ct, object_pk=obj_1.pk,
                flag_type="Broken thing",
                ip=ip, user_agent=user_agent, user=user, session_key=session_key)
        f2.save()

        try:
            flag, created = ContentFlag.objects.flag(request=request, object=self.user2,
                    flag_type='notworking', explanation="It really not go!")
            ok_(flag is not None)
            ok_(not created)
        except MultipleObjectsReturned, e:
            ok_(False, "MultipleObjectsReturned should not be raised")

    def test_basic_flag(self):
        """Exercise flagging with limit of one per unique request per unique object"""

        # Submit a flag.
        request = self.mk_request()
        flag, created = ContentFlag.objects.flag(request=request, object=self.user2,
                flag_type='notworking', explanation="It not go.")
        eq_(True, created)

        # One flag instance per unique user
        flag, created = ContentFlag.objects.flag(request=request, object=self.user2,
                flag_type='notworking', explanation="It really not go!")
        eq_(False, created)

        # Submit a flag on another object.
        request = self.mk_request()
        flag, created = ContentFlag.objects.flag(request=request, object=self.user1,
                flag_type='notworking', explanation="It not go.")
        eq_(True, created)

        # Try another unique request
        request = self.mk_request(ip='192.168.123.1')
        flag, created = ContentFlag.objects.flag(request=request, object=self.user2,
                flag_type='inappropriate', explanation="This is porn.")
        eq_(True, created)

        request = self.mk_request(ip='192.168.123.50', user_agent='Mozilla 1.0')
        flag, created = ContentFlag.objects.flag(request=request, object=self.user2,
                flag_type='inappropriate', explanation="This is porn.")
        eq_(True, created)

        eq_(4, len(ContentFlag.objects.all()))



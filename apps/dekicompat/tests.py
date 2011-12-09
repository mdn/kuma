# -*- coding: utf-8 -*-
from os.path import dirname
import logging

from urllib2 import Request
from requests.models import Response
import re

import mock
from nose import SkipTest
from nose.plugins.attrib import attr
from nose.tools import eq_

from test_utils import TestCase

import commonware

from django.conf import settings

from dekicompat.backends import DekiUser, DekiUserBackend


log = commonware.log.getLogger('mdn.dekicompat')

APP_DIR = dirname(__file__)
# Need to make test account fixture XML filename relative to this file, since
# working dir of running tests is not always the same.
TESTACCOUNT_FIXTURE_XML = ('%s/fixtures/testaccount.xml' % APP_DIR)
MULTI_ACCOUNT_FIXTURE_XML = ('%s/fixtures/email_multiple_users.xml' % APP_DIR)
SINGLE_ACCOUNT_FIXTURE_XML = ('%s/fixtures/email_single_user.xml' % APP_DIR)


def mockdekiauth(test):
    @mock.patch('requests.post')
    def test_new(self, mock_post):
        resp = Response()
        resp.status_code = 200
        resp.content = "authtoken_value"
        mock_post.return_value = resp
        test(self)
    return test_new


def mock_post_mindtouch_user(test):
    if settings.DEKIWIKI_MOCK:
        @mock.patch('dekicompat.backends.DekiUserBackend.post_mindtouch_user')
        def test_new(self, post_mindtouch_user):
            testaccount_fixture = open(TESTACCOUNT_FIXTURE_XML)
            user_info = DekiUser.parse_user_info(testaccount_fixture.read())
            post_mindtouch_user.return_value = user_info
            test(self)
        return test_new
    else:
        return test


def mock_put_mindtouch_user(test):
    if settings.DEKIWIKI_MOCK:
        @mock.patch('dekicompat.backends.DekiUserBackend.put_mindtouch_user')
        def test_new(self, put_mindtouch_user):
            testaccount_fixture = open(TESTACCOUNT_FIXTURE_XML)
            user_info = DekiUser.parse_user_info(testaccount_fixture.read())
            put_mindtouch_user.return_value = user_info
            test(self)
        return test_new
    else:
        return test


def mock_get_deki_user(test, fixture_file=TESTACCOUNT_FIXTURE_XML):
    if settings.DEKIWIKI_MOCK:
        @mock.patch('dekicompat.backends.DekiUserBackend.get_deki_user')
        def test_new(self, get_deki_user):
            testaccount_fixture = open(fixture_file)
            user_info = DekiUser.parse_user_info(testaccount_fixture.read())
            get_deki_user.return_value = user_info
            test(self)
        return test_new
    else:
        return test


def mock_get_deki_user_by_email(test, fixture_file=TESTACCOUNT_FIXTURE_XML):
    if settings.DEKIWIKI_MOCK:
        @mock.patch('dekicompat.backends.DekiUserBackend.get_deki_user_by_email')
        def test_new(self, get_deki_user_by_email):
            testaccount_fixture = open(fixture_file)
            user_info = DekiUser.parse_user_info(testaccount_fixture.read())
            get_deki_user_by_email.return_value = user_info
            test(self)
        return test_new
    else:
        return test


def mock_missing_get_deki_user(test):
    if settings.DEKIWIKI_MOCK:
        @mock.patch('dekicompat.backends.DekiUserBackend.get_deki_user')
        def test_new(self, get_deki_user):
            get_deki_user.return_value = None
            test(self)
        return test_new
    else:
        return test


def mock_mindtouch_login(test):
    if settings.DEKIWIKI_MOCK:
        @mock.patch('dekicompat.backends.DekiUserBackend.mindtouch_login')
        def test_new(self, mindtouch_login):
            mindtouch_login.return_value = 'fakeauthtoken'
            test(self)
        return test_new
    else:
        return test
    

class DekiCompatTestCase(TestCase):
    fixtures = ['test_users.json']
    # Don't use settings.DEKIWIKI_ENDPOINT tests always point at stage...
    stage_endpoint = 'http://developer-stage9.mozilla.org'
    auth_url = "%s/@api/deki/users/authenticate" % stage_endpoint
    username = 'test6'
    password = 'password'

    def setUp(self):
        self.authtoken_re = re.compile("\d+_\d+_[0-9A-Fa-f]+")

    def test_anonymous_request(self):
        "User doesn't have a deki authtoken Cookie."
        c = self.client
        r = c.get('/en-US/')

        user = r.context['request'].user
        self.assertEquals(True, user.is_anonymous())

    @mockdekiauth
    def test_good_mindtouch_login(self):
        authtoken = DekiUserBackend.mindtouch_login('user', 'pass')
        eq_('authtoken_value', authtoken)

    def test_unicode_mindtouch_login(self):
        raise SkipTest()
        u_str = u'\xe5\xe5\xee\xe9\xf8\xe7\u6709\u52b9'
        authtoken = DekiUserBackend.mindtouch_login('user', u_str)
        eq_('authtoken_value', authtoken)

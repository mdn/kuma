# -*- coding: utf-8 -*-
from urllib2 import Request
from requests.models import Response
import re

import mock
from nose.tools import eq_

from test_utils import TestCase

import commonware

from dekicompat.backends import DekiUserBackend

log = commonware.log.getLogger('kuma.dekicompat')


def mockdekiauth(test):
    @mock.patch('requests.post')
    def test_new(self, mock_post):
        resp = Response()
        resp.status_code = 200
        resp.content = "authtoken_value"
        mock_post.return_value = resp
        test(self)
    return test_new


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
        request = Request(self.__class__.auth_url)
        request.POST = {'username': 'user', 'password': 'pass'}
        authtoken = DekiUserBackend.mindtouch_login(request)
        eq_('authtoken_value', authtoken)

    def test_unicode_mindtouch_login(self):
        request = Request(self.__class__.auth_url)
        u_str = u'\xe5\xe5\xee\xe9\xf8\xe7\u6709\u52b9'
        request.POST = {'username': 'user', 'password': u_str}
        authtoken = DekiUserBackend.mindtouch_login(request)
        eq_('authtoken_value', authtoken)

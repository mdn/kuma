# -*- coding: utf-8 -*-
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, build_opener, urlopen, install_opener
import re

from django.contrib.auth.models import AnonymousUser, User

from test_utils import TestCase

import commonware

from devmo.models import UserProfile
from dekicompat.backends import DekiUserBackend, DekiUser

log = commonware.log.getLogger('kuma.dekicompat')

class DekiCompatTestCase(TestCase):
    """
    TODO: Some tests depend on A Dekiwiki server. Should we mock out 
    urllib2 instead?
    """

    fixtures = ['test_data.json']
    # Don't use settings.DEKIWIKI_ENDPOINT tests always point at stage...
    stage_endpoint = 'http://developer-stage9.mozilla.org'
    auth_url = "%s/@api/deki/users/authenticate" % stage_endpoint
    username = 'test6'
    password = 'password'     
    #TODO if username/password is bad, this causes python 2.6.5 to RuntimeError: maximum recursion depth exceeded while calling a Python object

    def setUp(self):
        self.authtoken_re = re.compile("\d+_\d+_[0-9A-Fa-f]+")

    def test_anonymous_request(self):
        "User doesn't have a deki authtoken Cookie."
        c = self.client
        r = c.get('/en-US/')

        user = r.context['request'].user
        self.assertEquals(True, user.is_anonymous())

    def test_good_deki_authtoken_request(self):
        """
        User was logged into Dekiwiki and so they are sending 
         an authtoken cookie. Middleware and Backend should
         be able to verify this token and load the user.
        """
        c = self.client
        c.cookies['authtoken'] = self.login_stage()
        r = c.get('/en-US/')

        user = r.context['request'].user
        self.assertEquals(False, user.is_anonymous())
        self.assertEquals(DekiCompatTestCase.username, user.username)
        users = User.objects.filter(username=DekiCompatTestCase.username)
        if not users:
            self.fail("Unable to retrieve User object")
        user = users[0]

        profile = user.get_profile()
        if not profile:
            self.fail("Unable to get user's profile")

        # Make sure we got back a new user and not 2 from the app/devmo/fixtures
        self.assertTrue(user.id > 2)
        self.assertTrue(profile.id > 3)
        self.assertTrue(profile.deki_user_id > 13)

    def test_bad_deki_authtoken_request(self):
        """
        Tries to authenticate a stale or bad authtoken
        """
        c = self.client
        c.cookies['authtoken'] = "42_666000666000666000_501e0057abbed0000be5e0005elf"
        r = c.get('/en-US/')

        user = r.context['request'].user
        self.assertEquals(True, user.is_anonymous())

    def login_stage(self):
        """
        Using the hardcoded username and password
        Attempts Dekiwiki login and returns an authtoken
        Example authtoken:
        252017_634285545555468650_3b7d87b75c5b0c0626ad8c9884e4398f
        """
        auth_url = self.__class__.auth_url
        username = self.__class__.username
        password = self.__class__.password

        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, auth_url, username, password)
        handler = HTTPBasicAuthHandler(password_mgr)
        opener = build_opener(handler)

        resp = opener.open(auth_url)
        authtoken = resp.read()

        if not authtoken or not self.authtoken_re.match(authtoken):
            self.fail("Unable to retrive an authtoken for user:%s password: %s at %s got %s" % (username, password, auth_url, str(authtoken)))
        return authtoken

    def test_get_or_create_user_already_exists(self):
        backend = DekiUserBackend()
        deki_user = DekiUser(13, 'hobo', 'Hobo McKee', 'almost@home.me', 'http://www.audienceoftwo.com/pics/upload/v1i6hobo.jpg')

        user = backend.get_or_create_user(deki_user)
        self.assertEquals(user.username, 'hobo')
        self.assertEquals(2, user.id)
        self.assertEquals(3, user.get_profile().id)
        self.assertEquals(13, user.get_profile().deki_user_id)

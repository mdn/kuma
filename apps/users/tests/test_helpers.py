import urllib
from hashlib import md5

from django.conf import settings
from django.contrib.auth.models import User

from jinja2 import Markup
from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from sumo.tests import TestCase
from users.helpers import (profile_url, profile_avatar, public_email,
                           display_name, user_list)
from devmo.models import UserProfile


class HelperTestCase(TestCase):
    def setUp(self):
        super(HelperTestCase, self).setUp()
        self.u = User.objects.create(pk=500000, username=u'testuser')

    def test_profile_url(self):
        eq_(u'/user/500000', profile_url(self.u))

    def test_profile_default_gravatar(self):
        ok_(urllib.urlencode({'d': settings.DEFAULT_AVATAR}) in profile_avatar(self.u), "Bad default avatar: %s" % profile_avatar(self.u))

    def test_profile_avatar(self):
        self.u.email = 'test@test.com'
        ok_(md5(self.u.email).hexdigest() in profile_avatar(self.u))

    def test_public_email(self):
        eq_(u'<span class="email">'
             '&#109;&#101;&#64;&#100;&#111;&#109;&#97;&#105;&#110;&#46;&#99;'
             '&#111;&#109;</span>', public_email('me@domain.com'))
        eq_(u'<span class="email">'
             '&#110;&#111;&#116;&#46;&#97;&#110;&#46;&#101;&#109;&#97;&#105;'
             '&#108;</span>', public_email('not.an.email'))

    def test_display_name(self):
        eq_(u'testuser', display_name(self.u))
        p = self.u.get_profile()
        p.fullname = u'Test User'
        eq_(u'Test User', display_name(self.u))

    def test_user_list(self):
        User.objects.create(pk=300000, username='testuser2')
        User.objects.create(pk=400000, username='testuser3')
        users = User.objects.all()
        list = user_list(users)
        assert isinstance(list, Markup)
        fragment = pq(list)
        eq_(3, len(fragment('a')))
        a = fragment('a')[1]
        assert a.attrib['href'].endswith('400000')
        eq_('testuser3', a.text)

import urllib
from hashlib import md5

from django.conf import settings
from django.contrib.auth.models import User

from jinja2 import Markup
from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from sumo.tests import TestCase
from devmo.urlresolvers import _prefixes

from ..helpers import profile_avatar, public_email, display_name, user_list
from ..models import UserProfile


class HelperTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(HelperTestCase, self).setUp()
        self.u = User.objects.get(username=u'testuser')

    def tearDown(self):
        super(HelperTestCase, self).tearDown()
        _prefixes.clear()

    def test_profile_default_gravatar(self):
        d_param = urllib.urlencode({'d': settings.DEFAULT_AVATAR})
        ok_(d_param in profile_avatar(self.u),
            "Bad default avatar: %s" % profile_avatar(self.u))

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
        new_user = User.objects.create(pk=40000, username='testuser3')
        eq_(u'testuser3', display_name(new_user))
        UserProfile.objects.create(user=new_user)
        p = new_user.get_profile()
        p.fullname = u'Test User'
        eq_(u'Test User', display_name(self.u))

    def test_user_list(self):
        User.objects.create(pk=400000, username='testuser3')
        users = User.objects.all()
        list = user_list(users)
        assert isinstance(list, Markup)
        fragment = pq(list)
        eq_(5, len(fragment('a')))
        a = fragment('a')[4]
        assert a.attrib['href'].endswith('testuser3')
        eq_('testuser3', a.text)

import urllib
from hashlib import md5

from django.conf import settings

from jinja2 import Markup
from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from . import UserTestCase, user
from ..helpers import gravatar_url, public_email, user_list


class HelperTestCase(UserTestCase):

    def setUp(self):
        super(HelperTestCase, self).setUp()
        self.u = self.user_model.objects.get(username=u'testuser')

    def test_profile_default_gravatar(self):
        d_param = urllib.urlencode({'d': settings.DEFAULT_AVATAR})
        ok_(d_param in gravatar_url(self.u),
            "Bad default avatar: %s" % gravatar_url(self.u))

    def test_gravatar_url(self):
        self.u.email = 'test@test.com'
        ok_(md5(self.u.email).hexdigest() in gravatar_url(self.u))

    def test_public_email(self):
        eq_('<span class="email">'
            '&#109;&#101;&#64;&#100;&#111;&#109;&#97;&#105;&#110;&#46;&#99;'
            '&#111;&#109;</span>', public_email('me@domain.com'))
        eq_('<span class="email">'
            '&#110;&#111;&#116;&#46;&#97;&#110;&#46;&#101;&#109;&#97;&#105;'
            '&#108;</span>', public_email('not.an.email'))

    def test_user_list(self):
        user(pk=400000, username='testuser3', save=True)
        users = self.user_model.objects.all()
        list = user_list(users)
        assert isinstance(list, Markup)
        fragment = pq(list)
        eq_(5, len(fragment('a')))
        a = fragment('a')[4]
        assert a.attrib['href'].endswith('testuser3')
        eq_('testuser3', a.text)

from hashlib import md5

from django.conf import settings
from django.utils.six.moves.urllib.parse import urlencode

from . import UserTestCase
from ..templatetags.jinja_helpers import gravatar_url, public_email


class HelperTestCase(UserTestCase):

    def setUp(self):
        super(HelperTestCase, self).setUp()
        self.u = self.user_model.objects.get(username=u'testuser')

    def test_default_gravatar(self):
        d_param = urlencode({'d': settings.DEFAULT_AVATAR})
        assert d_param in gravatar_url(self.u.email), \
            "Bad default avatar: %s" % gravatar_url(self.u.email)

    def test_gravatar_url(self):
        self.u.email = 'test@test.com'
        assert md5(self.u.email.encode('utf-8')).hexdigest() in gravatar_url(self.u.email)

    def test_public_email(self):
        assert ('<span class="email">'
                '&#109;&#101;&#64;&#100;&#111;&#109;&#97;&#105;&#110;&#46;&#99;'
                '&#111;&#109;</span>' == public_email('me@domain.com'))
        assert ('<span class="email">'
                '&#110;&#111;&#116;&#46;&#97;&#110;&#46;&#101;&#109;&#97;&#105;'
                '&#108;</span>' == public_email('not.an.email'))

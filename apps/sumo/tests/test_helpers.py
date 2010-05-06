# -*- coding: utf-8 -*-

from nose.tools import eq_

from django.test import TestCase
from django.contrib.auth.models import User

import jingo

from sumo.helpers import profile_url


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


class TestHelpers(TestCase):

    def setup(self):
        jingo.load_helpers()

    def test_fe_helper(self):
        context = {'var': '<bad>'}
        template = '{{ "<em>{t}</em>"|fe(t=var) }}'
        eq_('<em>&lt;bad&gt;</em>', render(template, context))

    def test_fe_positional(self):
        context = {'var': '<bad>'}
        template = '{{ "<em>{0}</em>"|fe(var) }}'
        eq_('<em>&lt;bad&gt;</em>', render(template, context))

    def test_fe_unicode(self):
        context = {'var': u'Français'}
        template = '{{ "Speak {0}"|fe(var) }}'
        eq_(u'Speak Français', render(template, context))

    def test_urlparams_unicode(self):
        context = {'var': u'Fran\xc3\xa7ais'}
        template = '{{ url("search")|urlparams(q=var) }}'
        eq_(u'/en-US/search?q=Fran%C3%A7ais', render(template, context))

    def test_profile_url(self):
        user = User.objects.create(username='testuser')
        eq_(profile_url(user),
            '/tiki-user_information.php?locale=en-US&userId=%s' % user.id)

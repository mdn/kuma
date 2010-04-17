# -*- coding: utf-8 -*-

from nose.tools import eq_

import jingo


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


def setup():
    jingo.load_helpers()


def test_fe_helper():
    context = {'var': '<bad>'}
    template = '{{ "<em>{t}</em>"|fe(t=var) }}'
    eq_('<em>&lt;bad&gt;</em>', render(template, context))


def test_fe_positional():
    context = {'var': '<bad>'}
    template = '{{ "<em>{0}</em>"|fe(var) }}'
    eq_('<em>&lt;bad&gt;</em>', render(template, context))


def test_fe_unicode():
    context = {'var': u'Français'}
    template = '{{ "Speak {0}"|fe(var) }}'
    eq_(u'Speak Français', render(template, context))


def test_urlparams_unicode():
    context = {'var': u'Fran\xc3\xa7ais'}
    template = '{{ url("search")|urlparams(q=var) }}'
    eq_(u'/en-US/search?q=Fran%C3%A7ais', render(template, context))

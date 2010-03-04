from nose.tools import eq_

from django.core.urlresolvers import reverse

import test_utils

import jingo

jingo.load_helpers()


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


def test_spellcheck_filter():
    r = 'right'
    w = 'worng'
    t = "{% if spellcheck(q, 'en-US') %}Yes{% else %}No{% endif %}"
    eq_('No', render(t, {'q': r}))
    eq_('Yes', render(t, {'q': w}))


def test_suggestions():
    """Suggestions should generate the right HTML."""
    url = '%s?%s' % (reverse('search'), 'q=worng')
    request = test_utils.RequestFactory().get(url)
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=wrong"><strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': w, 'request': request}))


def test_suggestions_page2():
    """Suggestions should reset page numbers to 1."""
    url = '%s?%s' % (reverse('search'), 'q=worng&page=2')
    request = test_utils.RequestFactory().get(url)
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=wrong&amp;page=1"><strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': w, 'request': request}))


def test_suggestions_categories():
    """Suggestions should respect MultiValueDict bits."""
    url = '%s?%s' % (reverse('search'), 'q=worng&category=1&category=2')
    request = test_utils.RequestFactory().get(url)
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=wrong&amp;category=1&amp;category=2"><strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': w, 'request': request}))


def test_suggestions_highlight():
    """Suggestions should not highlight correct words."""
    url = '%s?%s' % (reverse('search'), 'q=right worng')
    request = test_utils.RequestFactory().get(url)
    q = 'right worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=right+wrong">right <strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': q, 'request': request}))

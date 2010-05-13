from nose.tools import eq_

import test_utils
import jingo

from django import test

from sumo.urlresolvers import reverse


def setup():
    jingo.load_helpers()
    test.Client().get('/')


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


def test_spellcheck_filter():
    r = 'right'
    w = 'worng'
    t = "{% if spellcheck(q, 'en-US') %}Yes{% else %}No{% endif %}"
    eq_('Yes', render(t, {'q': r}))
    eq_('No', render(t, {'q': w}))


def test_spellcheck_custom():
    """Words in the custom dictionary should be accepted."""
    t = "{% if spellcheck(q, 'en-US') %}Yes{% else %}No{% endif %}"
    eq_('Yes', render(t, {'q': 'facebook'}))
    eq_('No', render(t, {'q': 'sumodev'}))


def test_suggestions():
    """Suggestions should generate the right HTML."""
    url = '%s?%s' % (reverse('search'), 'q=worng')
    request = test_utils.RequestFactory().get(url)
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp_ = '<a href="/en-US/search?q=wrong"><strong>wrong</strong></a>'
    eq_(exp_, render(t, {'q': w, 'request': request}))


def test_suggestions_page2():
    """Suggestions should reset page numbers to 1."""
    url = '%s?%s' % (reverse('search'), 'q=worng&page=2')
    request = test_utils.RequestFactory().get(url)
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp_ = '<a href="/en-US/search?q=wrong&amp;page=1"><strong>wrong</strong></a>'
    eq_(exp_, render(t, {'q': w, 'request': request}))


def test_suggestions_categories():
    """Suggestions should respect MultiValueDict bits."""
    url = '%s?%s' % (reverse('search'), 'q=worng&category=1&category=2')
    request = test_utils.RequestFactory().get(url)
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp_ = '<a href="/en-US/search?q=wrong&amp;category=1&amp;category=2"><strong>wrong</strong></a>'
    eq_(exp_, render(t, {'q': w, 'request': request}))


def test_suggestions_highlight():
    """Suggestions should not highlight correct words."""
    url = '%s?%s' % (reverse('search'), 'q=right worng')
    request = test_utils.RequestFactory().get(url)
    q = 'right worng'
    t = "{{ q|suggestions('en-US') }}"
    exp_ = '<a href="/en-US/search?q=right+wrong">right <strong>wrong</strong></a>'
    eq_(exp_, render(t, {'q': q, 'request': request}))

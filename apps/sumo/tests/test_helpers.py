from nose.tools import eq_

import test_utils

import jingo

jingo.load_helpers()

def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


def test_spellcheck():
    r = 'right'
    w = 'worng'
    t = "{% if spellcheck(q, 'en-US') %}Yes{% else %}No{% endif %}"
    eq_('No', render(t, {'q': r}))
    eq_('Yes', render(t, {'q': w}))


def test_suggestions():
    """Suggestions should generate the right HTML."""
    request = test_utils.RequestFactory().get('/en/search?q=worng')
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=wrong"><strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': w, 'request': request}))


def test_suggestions_page2():
    """Suggestions should reset page numbers to 1."""
    request = test_utils.RequestFactory().get('/en/search?q=worng&page=2')
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=wrong&amp;page=1"><strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': w, 'request': request}))


def test_suggestions_categories():
    """Suggestions should respect MultiValueDict bits."""
    req = '/en/search?q=worng&category=1&category=2'
    request = test_utils.RequestFactory().get(req)
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=wrong&amp;category=1&amp;category=2"><strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': w, 'request': request}))


def test_suggestions_highlight():
    """Suggestions should not highlight correct words."""
    req = '/en/search?q=right worng'
    request = test_utils.RequestFactory().get(req)
    q = 'right worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=right+wrong">right <strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': q, 'request': request}))

from nose.tools import eq_

import jingo


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
    w = 'worng'
    t = "{{ q|suggestions('en-US') }}"
    exp = '<a href="/en/search?q=wrong"><strong>wrong</strong></a>'
    eq_(exp, render(t, {'q': w}))

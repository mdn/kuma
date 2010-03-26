from nose.tools import eq_

import jingo


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


def test_fe_helper():
    context = {'var': '<bad>'}
    template = '{{ "<em>{t}</em>"|fe(t=var) }}'
    eq_('<em>&lt;bad&gt;</em>', render(template, context))

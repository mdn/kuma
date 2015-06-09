#!/usr/bin/env python

from translate.misc import dictutils


def test_add():
    d = dictutils.ordereddict()
    d[2] = 3
    assert len(d.order) == 1


def test_delete():
    d = dictutils.ordereddict()
    d[2] = 3
    del d[2]
    assert len(d.order) == 0


def test_pop():
    d = dictutils.ordereddict()
    d[2] = 3
    value = d.pop(2)
    assert len(d.order) == 0
    assert value == 3


def test_cidict_has_key():
    cid = dictutils.cidict()
    cid['lower'] = 'lowercase'
    assert 'lower' in cid
    assert 'Lower' in cid
    assert 'LOWER' in cid
    assert 'upper' not in cid

from nose.tools import eq_

from django.core.urlresolvers import reverse
from django.test.client import Client


def test_json_format():
    """JSON without callback should return application/json"""
    c = Client()
    response = c.get(reverse('search'), {
        'q': 'bookmarks',
        'format': 'json',
    })
    eq_(response['Content-Type'], 'application/json')


def test_json_callback_validation():
    """Various json callbacks -- validation"""
    c = Client()
    q = 'bookmarks'
    format = 'json'

    callbacks = (
        ('callback', 200),
        ('validCallback', 200),
        ('obj.method', 200),
        ('obj.someMethod', 200),
        ('arr[1]', 200),
        ('arr[12]', 200),
        ("alert('xss');foo", 400),
        ("eval('nastycode')", 400),
        ("someFunc()", 400),
        ('x', 200),
        ('x123', 200),
        ('$', 200),
        ('_func', 200),
        ('"></script><script>alert(\'xss\')</script>', 400),
        ('">', 400),
        ('var x=something;foo', 400),
        ('var x=', 400),
    )

    for callback, status in callbacks:
        response = c.get(reverse('search'), {
            'q': q,
            'format': format,
            'callback': callback,
        })
        eq_(response['Content-Type'], 'application/x-javascript')
        eq_(response.status_code, status)

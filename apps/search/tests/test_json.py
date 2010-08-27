from nose.tools import eq_

from sumo.urlresolvers import reverse
from sumo.tests import LocalizingClient

from .test_search import SphinxTestCase


class JSONTest(SphinxTestCase):
    def test_json_format(self):
        """JSON without callback should return application/json"""
        c = LocalizingClient()
        response = c.get(reverse('search'), {
            'q': 'bookmarks',
            'format': 'json',
        })
        eq_(response['Content-Type'], 'application/json')

    def test_json_callback_validation(self):
        """Various json callbacks -- validation"""
        c = LocalizingClient()
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

    def test_json_empty_query(self):
        """Empty query returns JSON format"""
        c = LocalizingClient()

        # Test with flags for advanced search or not
        a_types = (0, 1, 2)
        for a in a_types:
            response = c.get(reverse('search'), {
                'format': 'json', 'a': a,
            })
            eq_(response['Content-Type'], 'application/json')


def test_json_down():
    """When the Sphinx is down, return JSON and 503 status"""
    c = LocalizingClient()

    # Test with flags for advanced search or not
    callbacks = (
        ('', 503, 'application/json'),
        ('validCallback', 503, 'application/x-javascript'),
        # Invalid callback does not search
        ('eval("xss");a', 400, 'application/x-javascript'),
    )
    for callback, status, mimetype in callbacks:
        response = c.get(reverse('search'), {
            'q': 'json down', 'format': 'json',
            'callback': callback,
        })
        eq_(response['Content-Type'], mimetype)
        eq_(response.status_code, status)

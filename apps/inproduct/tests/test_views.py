from urlparse import urlparse

from nose.tools import eq_

from sumo.tests import TestCase


class RedirectTestCase(TestCase):
    fixtures = ['inproduct/redirects.json']
    test_urls = (
        ('firefox/3.6.12/WINNT/en-US/', '/en-US/home'),
        ('mobile/4.0/Android/en-US/', '/en-US/mobile'),
        ('firefox/3.6.12/MACOSX/en-US', '/en-US/home'),
        ('firefox/3.6.12/WINNT/fr/', '/fr/home'),
        ('firefox/3.6.12/WINNT/fr-FR/', '/fr/home'),
        ('firefox-home/1.1/iPhone/en-US/', '/en-US/firefox-home'),
        ('firefox/4.0/Linux/en-US/prefs-applications',
            '/en-US/kb/Applications'),
        ('firefox/4.0/Linux/en-US/prefs-applications/',
            '/en-US/kb/Applications'),
        ('firefox/5.0/NONE/en-US/', '/en-US/does-not-exist'),
        ('mobile/4.0/MARTIAN/en-US/', 'http://martian.com'),
        ('mobile/4.0/martian/en-US/', 'http://martian.com'),
        ('firefox/4.0/Android/en-US/foo', 404),
    )

    test_eu_urls = (
        ('firefox/3.6.12/WINNT/en-US/eu/', '/en-US/home'),
        ('mobile/4.0/Android/en-US/eu/', '/en-US/mobile'),
        ('firefox/3.6.12/MACOSX/en-US/eu', '/en-US/home'),
        ('firefox/3.6.12/WINNT/fr/eu/', '/fr/home'),
        ('firefox/3.6.12/WINNT/fr-FR/eu/', '/fr/home'),
        ('firefox-home/1.1/iPhone/en-US/eu/', '/en-US/firefox-home'),
        ('firefox/4.0/Linux/en-US/eu/prefs-applications',
            '/en-US/kb/Applications'),
        ('firefox/4.0/Linux/en-US/eu/prefs-applications/',
            '/en-US/kb/Applications'),
        ('firefox/5.0/NONE/en-US/eu/', '/en-US/does-not-exist'),
        ('mobile/4.0/MARTIAN/en-US/eu/', 'http://martian.com'),
        ('mobile/4.0/martian/en-US/eu/', 'http://martian.com'),
        ('firefox/4.0/Android/en-US/eu/foo', 404),
    )

    def test_target(self):
        """Test that we can vary on any parameter and targets work."""
        self._targets(self.test_urls, 'as=u')

    def test_eu_target(self):
        """Test that all URLs work with the extra 'eu'."""
        self._targets(self.test_eu_urls, 'eu=1&as=u')

    def _targets(self, urls, querystring):
        for input, output in urls:
            response = self.client.get(u'/1/%s' % input, follow=True)
            if output == 404:
                eq_(404, response.status_code)
            elif output.startswith('http'):
                chain = [u[0] for u in response.redirect_chain]
                assert output in chain
            else:
                r = response.redirect_chain
                r.reverse()
                final = urlparse(r[0][0])
                eq_(output, final.path)
                eq_(querystring, final.query)

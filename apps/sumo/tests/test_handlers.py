from django.test import Client, TestCase


class TestHandlers(TestCase):
    client = Client()

    def test_404_strip_slash(self):
        """Requesting a URL with a trailing slash should remove the slash
        and redirect."""
        response = self.client.get('/en-US/search/', follow=True)
        self.assertRedirects(response, '/en-US/search', status_code=301)

    def test_404_preserve_query_string(self):
        """A redirect stripping a slash should not change the query
        string."""
        response = self.client.get('/en-US/search/?q=a+test', follow=False)
        self.assertEquals('http://testserver/en-US/search?q=a+test',
                          response._headers.get('location')[1])
        self.assertEquals(301, response.status_code)

        # Once more, with Unicode, just for fun.
        response = self.client.get('/en-US/search/?q=fran%C3%A7ais',
                                   follow=False)
        self.assertEquals('http://testserver/en-US/search?q=fran%C3%A7ais',
                          response._headers.get('location')[1])
        self.assertEquals(301, response.status_code)

    def test_real_404_status(self):
        """Requesting a real undefined URL should still be a 404."""
        response = self.client.get('/en-US/no-view')
        self.assertEquals(404, response.status_code)

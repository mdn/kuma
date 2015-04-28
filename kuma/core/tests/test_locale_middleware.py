from kuma.core.tests import KumaTestCase


class TestLocaleMiddleware(KumaTestCase):
    def test_default_redirect(self):
        # User wants en-us, we send en-US
        response = self.client.get('/', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='en-us')
        self.assertRedirects(response, '/en-US/', status_code=301)

        # User wants fr-FR, we send fr
        response = self.client.get('/', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='fr-fr')
        self.assertRedirects(response, '/fr/', status_code=301)

        # User wants xx, we send en-US
        response = self.client.get('/', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='xx')
        self.assertRedirects(response, '/en-US/', status_code=301)

        # User doesn't know what they want, we send en-US
        response = self.client.get('/', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='')
        self.assertRedirects(response, '/en-US/', status_code=301)

    def test_mixed_case_header(self):
        """Accept-Language is case insensitive."""
        response = self.client.get('/', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='en-US')
        self.assertRedirects(response, '/en-US/', status_code=301)

    def test_specificity(self):
        """Requests for /fr-FR/ should end up on /fr/"""
        reponse = self.client.get('/fr-FR/', follow=True)
        self.assertRedirects(reponse, '/fr/', status_code=301)

    def test_partial_redirect(self):
        """Ensure that /en/ gets directed to /en-US/."""
        response = self.client.get('/en/', follow=True)
        self.assertRedirects(response, '/en-US/', status_code=301)

    def test_lower_to_upper(self):
        """/en-us should redirect to /en-US."""
        response = self.client.get('/en-us/', follow=True)
        self.assertRedirects(response, '/en-US/', status_code=301)

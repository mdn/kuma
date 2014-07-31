import requests

from allauth.socialaccount.providers.oauth2.views import (OAuth2LoginView,
                                                          OAuth2CallbackView)
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter


class KumaGitHubOAuth2Adapter(GitHubOAuth2Adapter):
    """
    A custom GitHub OAuth adapter to be used for fetching the list
    of private email addresses stored for the given user at GitHub.

    We store those email addresses in the extra data of each account.
    """
    email_url = 'https://api.github.com/user/emails'

    def complete_login(self, request, app, token, **kwargs):
        with requests.Session() as session:
            session.params = {'access_token': token.token}
            profile_data = session.get(self.profile_url)
            extra_data = profile_data.json()
            email_data = session.get(self.email_url)
            extra_data['email_addresses'] = email_data.json()
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)


oauth2_login = OAuth2LoginView.adapter_view(KumaGitHubOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(KumaGitHubOAuth2Adapter)

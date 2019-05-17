from allauth.account.utils import get_next_redirect_url
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (OAuth2CallbackView,
                                                          OAuth2LoginView)

from kuma.core.decorators import redirect_in_maintenance_mode
from kuma.core.urlresolvers import reverse
from kuma.core.utils import requests_retry_session


class KumaGitHubOAuth2Adapter(GitHubOAuth2Adapter):
    """
    A custom GitHub OAuth adapter to be used for fetching the list
    of private email addresses stored for the given user at GitHub.

    We store those email addresses in the extra data of each account.
    """
    email_url = 'https://api.github.com/user/emails'

    def complete_login(self, request, app, token, **kwargs):
        session = requests_retry_session()
        params = {'access_token': token.token}
        profile_data = session.get(self.profile_url, params=params)
        profile_data.raise_for_status()
        extra_data = profile_data.json()
        email_data = session.get(self.email_url, params=params)
        email_data.raise_for_status()
        extra_data['email_addresses'] = email_data.json()
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)


class KumaOAuth2LoginView(OAuth2LoginView):

    def dispatch(self, request):
        next_url = (get_next_redirect_url(request) or
                    reverse('users.my_edit_page'))
        request.session['sociallogin_next_url'] = next_url
        request.session.modified = True
        return super(KumaOAuth2LoginView, self).dispatch(request)


oauth2_login = redirect_in_maintenance_mode(
    KumaOAuth2LoginView.adapter_view(KumaGitHubOAuth2Adapter)
)
oauth2_callback = redirect_in_maintenance_mode(
    OAuth2CallbackView.adapter_view(KumaGitHubOAuth2Adapter)
)

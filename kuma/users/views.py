from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)

from kuma.users.models import UserProfile


class NoPromptOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    def get_extra_params(self, request):
        params = {"next": "/en-US/plus"}
        email = request.GET.get("email")
        if email:
            # Note that "prompt=none" will fail if "login_hint"
            # is not also provided with the user's correct email.
            params.update(prompt="none", login_hint=email)
        return params


no_prompt_login = NoPromptOIDCAuthenticationRequestView.as_view()


class KumaOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    @property
    def success_url(self):
        try:
            profile = UserProfile.objects.get(user=self.user)
            is_subscriber = profile.is_subscriber
        except UserProfile.DoesNotExist:
            is_subscriber = False

        # Redirect new users to Plus.
        if self.request.get("created") and not is_subscriber:
            return "/en-US/plus"
        return super().success_url

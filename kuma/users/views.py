from mozilla_django_oidc.views import OIDCAuthenticationRequestView


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

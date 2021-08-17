from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from mozilla_django_oidc.middleware import SessionRefresh


def subscribe(request):
    return redirect(settings.SUBSCRIPTION_SUBSCRIBE_URL)


def settings_(request):
    return redirect(settings.SUBSCRIPTION_SETTINGS_URL)


class KumaSessionRefresh(SessionRefresh):
    def is_refreshable_url(self, request):
        return True

    def process_request(self, request):
        # Trick the SessionRefresh middleware to pretend the user hasn't
        # logged in in ages.
        request.session["oidc_id_token_expiration"] = 0
        return super().process_request(request)


def download(request):
    """If you view this, that means you probably clicked the 'Click here to download'
    on the sub plat page. That means, most possibly, that you have just recently
    typed in your credit card and you're now a FxA Sub Plat subscriber.
    But Kuma might not know, so lets send the user to authenticate one more time.
    """
    middleware = KumaSessionRefresh()
    response = middleware.process_request(request)
    if isinstance(response, HttpResponseRedirect):
        # This response should have a 302 redirect URL on it that
        # includes `prompt=none`.
        print("Redirecting...", response.url)
        return response
    else:
        print("Response is not a HttpResponse", response)

    return redirect("/users/fxa/login/authenticate/")

from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import urlencode


def subscribe(request):
    return redirect(settings.SUBSCRIPTION_SUBSCRIBE_URL)


def settings_(request):
    return redirect(settings.SUBSCRIPTION_SETTINGS_URL)


def download(request):
    """If you view this, that means you probably clicked the 'Click here to download'
    on the sub plat page. That means, most possibly, that you have just recently
    typed in your credit card and you're now a FxA Sub Plat subscriber.
    But Kuma might not know, so lets send the user to authenticate one more time.
    """
    params = {"prompt": "none"}
    qs = urlencode(params)
    return redirect(f"/users/fxa/login/authenticate/?{qs}")

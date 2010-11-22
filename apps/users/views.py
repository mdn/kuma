import urlparse

from django import http
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect

import jingo

from sumo.decorators import ssl_required


@ssl_required
def login(request):
    """Try to log the user in."""
    auth.logout(request)
    next_url = _clean_next_url(request) or settings.LOGIN_REDIRECT_URL

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            auth.login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(next_url)
    else:
        form = AuthenticationForm(request)

    request.session.set_test_cookie()

    return jingo.render(request, 'users/login.html',
                        {'form': form, 'next_url': next_url})


@ssl_required
def logout(request):
    """Log the user out."""
    auth.logout(request)
    next_url = _clean_next_url(request) if 'next' in request.GET else ''

    return http.HttpResponseRedirect(next_url or settings.LOGOUT_REDIRECT_URL)


def _clean_next_url(request):
    if 'next' in request.POST:
        url = request.POST.get('next')
    elif 'next' in request.GET:
        url = request.GET.get('next')
    else:
        url = request.META.get('HTTP_REFERER')

    if url:
        parsed_url = urlparse.urlparse(url)
        # Don't redirect outside of SUMO
        if parsed_url.scheme:
            site_domain = Site.objects.get_current().domain
            url_domain = parsed_url.netloc
            if site_domain != url_domain:
                url = None

        # Don't redirect right back to login or logout page
        if parsed_url.path in [settings.LOGIN_URL, settings.LOGOUT_URL]:
            url = None

    return url

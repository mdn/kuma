import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, QueryDict
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST

from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.helpers import render_authentication_error
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount import app_settings, providers

from kuma.core.urlresolvers import reverse
from kuma.core.decorators import never_cache

from .provider import PersonaProvider


@never_cache
@require_GET
def persona_csrf(request):
    """Fetch a CSRF token for the frontend JavaScript."""
    # Bluntly stolen from django-browserid
    csrf_token = get_token(request)
    return HttpResponse(csrf_token)


@require_POST
def persona_login(request):
    """
    This is a view to work around an optimization in the Zeus load balancer
    that doesn't allow creating session cookies on the frontpage.

    We're stash the Persona assertion in the session and trigger setting
    the session cookie by that. We then redirect to the real persona login
    view called "persona_complete" to complete the Perona steps.
    """
    # REDFLAG FIXME TODO GODDAMNIT
    request.session['sociallogin_assertion'] = request.POST.get('assertion', '')
    querystring = QueryDict('', mutable=True)
    for param in ('next', 'process'):
        querystring[param] = request.POST.get(param, '')
    return redirect('%s?%s' % (reverse('persona_complete'),
                               querystring.urlencode('/')))


def persona_complete(request):
    assertion = request.session.pop('sociallogin_assertion', '')
    provider_settings = app_settings.PROVIDERS.get(PersonaProvider.id, {})
    audience = provider_settings.get('AUDIENCE', None)
    if audience is None:
        raise ImproperlyConfigured("No Persona audience configured. Please "
                                   "add an AUDIENCE item to the "
                                   "SOCIALACCOUNT_PROVIDERS['persona'] setting.")

    resp = requests.post(settings.PERSONA_VERIFIER_URL,
                         {'assertion': assertion,
                          'audience': audience})
    try:
        resp.raise_for_status()
        extra_data = resp.json()
        if extra_data['status'] != 'okay':
            return render_authentication_error(
                request,
                provider_id=PersonaProvider.id,
                extra_context={'response': extra_data})
    except (ValueError, requests.RequestException) as e:
        return render_authentication_error(
            request,
            provider_id=PersonaProvider.id,
            exception=e)
    login = providers.registry \
        .by_id(PersonaProvider.id) \
        .sociallogin_from_response(request, extra_data)
    login.state = SocialLogin.state_from_request(request)
    return complete_social_login(request, login)

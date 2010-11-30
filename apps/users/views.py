import urlparse

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.utils.http import base36_to_int

import jingo

from sumo.decorators import ssl_required, logout_required
from sumo.urlresolvers import reverse
from users.backends import Sha256Backend  # Monkey patch User.set_password.
from users.forms import RegisterForm, AuthenticationForm


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

    return HttpResponseRedirect(next_url or settings.LOGOUT_REDIRECT_URL)


@ssl_required
@logout_required
@require_http_methods(['GET', 'POST'])
def register(request):
    """Register a new user."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # TODO: Send registration email for confirmation.
            user.is_active = True
            user.set_password(form['password1'].data)
            user.save()
            return jingo.render(request, 'users/register_done.html')
    else:  # request.method == 'GET'
        form = RegisterForm()
    return jingo.render(request, 'users/register.html',
                        {'form': form})


# Password reset views are based on django.contrib.auth.views.
# 4 views for password reset:
# - password_reset sends the mail
# - password_reset_sent shows a success message for the above
# - password_reset_confirm checks the link the user clicked and
#   prompts for a new password
# - password_reset_complete shows a success message for the above
@ssl_required
def password_reset(request):
    """Password reset form."""
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(use_https=request.is_secure(),
                      token_generator=default_token_generator,
                      email_template_name='users/email/pw_reset.ltxt')
            return HttpResponseRedirect(reverse('users.pw_reset_sent'))
    else:
        form = PasswordResetForm()

    return jingo.render(request, 'users/pw_reset_form.html', {'form': form})


def password_reset_sent(request):
    """Password reset email sent."""
    return jingo.render(request, 'users/pw_reset_sent.html')


@ssl_required
def password_reset_confirm(request, uidb36=None, token=None):
    """View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    try:
        uid_int = base36_to_int(uidb36)
    except ValueError:
        raise Http404

    user = get_object_or_404(User, id=uid_int)
    context = {}

    if default_token_generator.check_token(user, token):
        context['validlink'] = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('users.pw_reset_complete'))
        else:
            form = SetPasswordForm(None)
    else:
        context['validlink'] = False
        form = None
    context['form'] = form
    return jingo.render(request, 'users/pw_reset_confirm.html', context)


def password_reset_complete(request):
    """Password reset complete."""
    return jingo.render(request, 'users/pw_reset_complete.html')


def _clean_next_url(request):
    if 'next' in request.POST:
        url = request.POST.get('next')
    elif 'next' in request.GET:
        url = request.GET.get('next')
    else:
        url = request.META.get('HTTP_REFERER')

    if url:
        parsed_url = urlparse.urlparse(url)
        # Don't redirect outside of SUMO.
        # Don't include protocol+domain, so if we are https we stay that way.
        if parsed_url.scheme:
            site_domain = Site.objects.get_current().domain
            url_domain = parsed_url.netloc
            if site_domain != url_domain:
                url = None
            else:
                url = u'?'.join([getattr(parsed_url, x) for x in
                                ('path', 'query') if getattr(parsed_url, x)])

        # Don't redirect right back to login or logout page
        if parsed_url.path in [settings.LOGIN_URL, settings.LOGOUT_URL]:
            url = None

    return url

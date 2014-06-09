import os
import urlparse

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.forms import (SetPasswordForm,
                                       PasswordChangeForm,
                                       PasswordResetForm)
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.decorators.http import (require_http_methods, require_GET,
                                          require_POST)
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters

from django.shortcuts import get_object_or_404, render
from django.utils.http import base36_to_int, is_safe_url

from django_browserid.forms import BrowserIDForm
from django_browserid.auth import get_audience
from django_browserid import auth as browserid_auth

from access.decorators import logout_required, login_required
import constance.config
from tidings.tasks import claim_watches
from waffle import switch_is_active

from sumo.decorators import ssl_required
from sumo.urlresolvers import reverse, split_path
from users.forms import (ProfileForm, AvatarForm, EmailConfirmationForm,
                         AuthenticationForm, EmailChangeForm,
                         BrowserIDRegisterForm,
                         EmailReminderForm, UserBanForm)
from users.models import Profile, RegistrationProfile, EmailChange, UserBan
from users.tasks import send_welcome_email
from users.utils import handle_login, handle_register, send_reminder_email
from devmo.models import UserProfile
from devmo.forms import newsletter_subscribe

SESSION_VERIFIED_EMAIL = getattr(settings, 'BROWSERID_SESSION_VERIFIED_EMAIL',
                                 'browserid_verified_email')
SESSION_REDIRECT_TO = getattr(settings, 'BROWSERID_SESSION_REDIRECT_TO',
                              'browserid_redirect_to')


def _verify_browserid(form, request):
    """Verify submitted BrowserID assertion.

    This is broken out into a standalone function because it will probably
    change in the near future if the django-browserid API changes, and it's
    handy to mock out in tests this way."""
    assertion = form.cleaned_data['assertion']
    backend = browserid_auth.BrowserIDBackend()
    result = backend.verify(assertion, get_audience(request))
    return result


def _get_latest_user_with_email(email):
    users = User.objects.filter(email=email).order_by('-last_login')
    if len(users) > 0:
        return users[0]
    else:
        return None


def set_browserid_explained(response):
    response.set_cookie('browserid_explained', 1, max_age=31536000)
    return response


@csrf_exempt
@ssl_required
@login_required
@require_POST
def browserid_change_email(request):
    """Process a submitted BrowserID assertion to change email."""
    form = BrowserIDForm(data=request.POST)
    if not form.is_valid():
        messages.error(request, form.errors)
        return HttpResponseRedirect(reverse('users.change_email'))
    result = _verify_browserid(form, request)
    email = result['email']
    user = _get_latest_user_with_email(email)
    if user and user != request.user:
        messages.error(request, 'That email already belongs to another '
                       'user.')
        return HttpResponseRedirect(reverse('users.change_email'))
    else:
        user = request.user
        user.email = email
        user.save()
        return HttpResponseRedirect(reverse('devmo_profile_edit',
                                            args=[user.username, ]))


@ssl_required
def browserid_realm(request):
    # serve the realm from the environment config
    return HttpResponse(constance.config.BROWSERID_REALM_JSON,
                        content_type='application/json')


@csrf_exempt
@ssl_required
@require_POST
@sensitive_post_parameters()
def browserid_verify(request):
    """Process a submitted BrowserID assertion.

    If valid, try to find a Django user that matches the verified
    email address. If not found, we bounce to a profile creation page
    (ie. browserid_register)."""
    redirect_to = (_clean_next_url(request) or
            getattr(settings, 'LOGIN_REDIRECT_URL', reverse('home')))
    redirect_to_failure = (_clean_next_url(request) or
            getattr(settings, 'LOGIN_REDIRECT_URL_FAILURE', reverse('home')))

    failure_resp = set_browserid_explained(
        HttpResponseRedirect(redirect_to_failure))

    # If the form's not valid, then this is a failure.
    form = BrowserIDForm(data=request.POST)
    if not form.is_valid():
        return failure_resp

    # If the BrowserID assersion is not valid, then this is a failure.
    result = _verify_browserid(form, request)
    if not result:
        return failure_resp

    # So far, so good: We have a verified email address. But, no user, yet.
    email = result['email']
    user = None

    # Look for first most recently used Django account, use if found.
    user = _get_latest_user_with_email(email)

    # If we got a user from either the Django or MT paths, complete login for
    # Django and MT and redirect.
    if user:
        user.backend = 'django_browserid.auth.BrowserIDBackend'
        auth.login(request, user)
        return set_browserid_explained(HttpResponseRedirect(redirect_to))

    # Retain the verified email in a session, redirect to registration page.
    request.session[SESSION_VERIFIED_EMAIL] = email
    request.session[SESSION_REDIRECT_TO] = redirect_to
    return set_browserid_explained(
        HttpResponseRedirect(reverse('users.browserid_register')))


@ssl_required
@sensitive_post_parameters('password')
def browserid_register(request):
    """Handle user creation when assertion is valid, but no existing user"""
    redirect_to = request.session.get(SESSION_REDIRECT_TO,
        getattr(settings, 'LOGIN_REDIRECT_URL', reverse('home')))
    email = request.session.get(SESSION_VERIFIED_EMAIL, None)

    if not email:
        # This is pointless without a verified email.
        return HttpResponseRedirect(redirect_to)

    # Set up the initial forms
    register_form = BrowserIDRegisterForm(request.locale)
    login_form = AuthenticationForm()

    if request.method == 'POST':
        # If the profile creation form was submitted...
        if 'register' == request.POST.get('action', None):
            register_form = BrowserIDRegisterForm(request.locale, request.POST)
            if register_form.is_valid():
                # If the registration form is valid, then create a new
                # Django user.
                # TODO: This all belongs in model classes
                username = register_form.cleaned_data['username']

                user = User.objects.create(username=username, email=email)
                user.set_unusable_password()
                user.save()

                profile = UserProfile.objects.create(user=user)
                profile.save()

                user.backend = 'django_browserid.auth.BrowserIDBackend'
                auth.login(request, user)

                if switch_is_active('welcome_email'):
                    send_welcome_email.delay(user.pk)

                newsletter_subscribe(request, email,
                                     register_form.cleaned_data)
                redirect_to = request.session.get(SESSION_REDIRECT_TO,
                                                  profile.get_absolute_url())
                return set_browserid_explained(HttpResponseRedirect(redirect_to))

    # HACK: Pretend the session was modified. Otherwise, the data disappears
    # for the next request.
    request.session.modified = True

    return render(request, 'users/browserid_register.html',
                        {'login_form': login_form,
                         'register_form': register_form})


@ssl_required
@xframe_options_sameorigin
@sensitive_post_parameters('password')
def login(request):
    """Try to log the user in."""
    next_url = _clean_next_url(request)
    if request.method == 'GET' and request.user.is_authenticated():
        if next_url:
            return HttpResponseRedirect(next_url)
    else:
        next_url = _clean_next_url(request) or reverse('home')
    form = handle_login(request)

    if form.is_valid() and request.user.is_authenticated():
        next_url = next_url or reverse('home')
        return HttpResponseRedirect(next_url)

    return render(request, 'users/login.html',
                            {'form': form, 'next_url': next_url})


@ssl_required
def logout(request):
    """Log the user out."""
    username = request.user.username

    auth.logout(request)
    next_url = _clean_next_url(request, username) or reverse('home')

    resp = HttpResponseRedirect(next_url)
    resp.delete_cookie('authtoken')
    return resp


@ssl_required
@logout_required
@require_http_methods(['GET', 'POST'])
@sensitive_post_parameters('password', 'password2')
def register(request):
    """Register a new user."""
    form = handle_register(request)
    if form.is_valid():
        return render(request, 'users/register_done.html')
    return render(request, 'users/register.html',
                  {'form': form})


def activate(request, activation_key):
    """Activate a User account."""
    activation_key = activation_key.lower()
    account = RegistrationProfile.objects.activate_user(activation_key)
    my_questions = None
    form = AuthenticationForm()
    if account:
        # Claim anonymous watches belonging to this email
        claim_watches.delay(account)

        # my_questions = Question.objects.filter(creator=account)
        # TODO: remove this after dropping unconfirmed questions.
        # my_questions.update(status=CONFIRMED)
    return render(request, 'users/activate.html',
                  {'account': account, 'questions': my_questions,
                   'form': form})


def resend_confirmation(request):
    """Resend confirmation email."""
    if request.method == 'POST':
        form = EmailConfirmationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                reg_prof = RegistrationProfile.objects.get(
                    user__email=email, user__is_active=False)
                RegistrationProfile.objects.send_confirmation_email(reg_prof)
            except RegistrationProfile.DoesNotExist:
                # Don't leak existence of email addresses.
                pass
            return render(request, 'users/resend_confirmation_done.html',
                          {'email': email})
    else:
        form = EmailConfirmationForm()
    return render(request, 'users/resend_confirmation.html', {'form': form})


def send_email_reminder(request):
    """Send reminder email."""
    if request.method == 'POST':
        form = EmailReminderForm(request.POST)
        if form.is_valid():
            error = None
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username, is_active=True)
                if user.email:
                    send_reminder_email(user)
                else:
                    error = 'no_email'
            except User.DoesNotExist:
                # Don't leak existence of email addresses.
                pass
            return render(request, 'users/send_email_reminder_done.html',
                          {'username': username, 'error': error})
    else:
        form = EmailConfirmationForm()
    return render(request, 'users/resend_confirmation.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def change_email(request):
    """Change user's email. Send confirmation first."""
    if request.method == 'POST':
        form = EmailChangeForm(request.user, request.POST)
        u = request.user
        if form.is_valid() and u.email != form.cleaned_data['email']:
            # Delete old registration profiles.
            EmailChange.objects.filter(user=request.user).delete()
            # Create a new registration profile and send a confirmation email.
            email_change = EmailChange.objects.create_profile(
                user=request.user, email=form.cleaned_data['email'])
            EmailChange.objects.send_confirmation_email(
                email_change, form.cleaned_data['email'])
            return render(request, 'users/change_email_done.html',
                          {'email': form.cleaned_data['email']})
    else:
        form = EmailChangeForm(request.user,
                               initial={'email': request.user.email})
    return render(request, 'users/change_email.html', {'form': form})


@require_GET
def confirm_change_email(request, activation_key):
    """Confirm the new email for the user."""
    activation_key = activation_key.lower()
    email_change = get_object_or_404(EmailChange,
                                     activation_key=activation_key)
    u = email_change.user
    old_email = u.email

    # Check that this new email isn't a duplicate in the system.
    new_email = email_change.email
    duplicate = User.objects.filter(email=new_email).exists()
    if not duplicate:
        # Update user's email.
        u.email = new_email
        u.save()

    # Delete the activation profile now, we don't need it anymore.
    email_change.delete()

    return render(request, 'users/change_email_complete.html',
                  {'old_email': old_email, 'new_email': new_email,
                   'username': u.username, 'duplicate': duplicate})


def profile(request, user_id):
    user_profile = get_object_or_404(UserProfile, user__id=user_id)
    return render(request, 'users/profile.html', {'profile': user_profile})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_profile(request):
    """Edit user profile."""
    try:
        user_profile = request.user.get_profile()
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            user_profile = form.save()
            return HttpResponseRedirect(reverse('users.profile',
                                                args=[request.user.id]))
    else:  # request.method == 'GET'
        form = ProfileForm(instance=user_profile)

    return render(request, 'users/edit_profile.html',
                  {'form': form, 'profile': user_profile})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_avatar(request):
    """Edit user avatar."""
    try:
        user_profile = request.user.get_profile()
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        # Upload new avatar and replace old one.
        old_avatar_path = None
        if user_profile.avatar:
            # Need to store the path, not the file here, or else django's
            # form.is_valid() messes with it.
            old_avatar_path = user_profile.avatar.path
        form = AvatarForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            if old_avatar_path:
                os.unlink(old_avatar_path)
            user_profile = form.save()

            # Delete uploaded avatar and replace with thumbnail.
            name = user_profile.avatar.name
            user_profile.avatar.delete()
            user_profile.avatar.save(name, content, save=True)
            return HttpResponseRedirect(reverse('users.edit_profile'))

    else:  # request.method == 'GET'
        form = AvatarForm(instance=user_profile)

    return render(request, 'users/edit_avatar.html',
                  {'form': form, 'profile': user_profile})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_avatar(request):
    """Delete user avatar."""
    try:
        user_profile = request.user.get_profile()
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        # Delete avatar here
        if user_profile.avatar:
            user_profile.avatar.delete()
        return HttpResponseRedirect(reverse('users.edit_profile'))
    # else:  # request.method == 'GET'

    return render(request, 'users/confirm_avatar_delete.html',
                  {'profile': user_profile})


@sensitive_post_parameters()
def password_reset(request):
    """Password reset form.

    Based on django.contrib.auth.views. This view sends the email.

    """
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(use_https=request.is_secure(),
                      token_generator=default_token_generator,
                      email_template_name='users/email/pw_reset.ltxt')
        # Don't leak existence of email addresses.
        return HttpResponseRedirect(reverse('users.pw_reset_sent'))
    else:
        form = PasswordResetForm()

    return render(request, 'users/pw_reset_form.html', {'form': form})


def password_reset_sent(request):
    """Password reset email sent.

    Based on django.contrib.auth.views. This view shows a success message after
    email is sent.

    """
    return render(request, 'users/pw_reset_sent.html')


@ssl_required
@sensitive_post_parameters()
def password_reset_confirm(request, uidb36=None, token=None):
    """View that checks the hash in a password reset link and presents a
    form for entering a new password.

    Based on django.contrib.auth.views.

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
    return render(request, 'users/pw_reset_confirm.html', context)


def password_reset_complete(request):
    """Password reset complete.

    Based on django.contrib.auth.views. Show a success message.

    """
    form = AuthenticationForm()
    return render(request, 'users/pw_reset_complete.html', {'form': form})


@login_required
def password_change(request):
    """Change password form page."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('users.pw_change_complete'))
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'users/pw_change.html', {'form': form})


@login_required
def password_change_complete(request):
    """Change password complete page."""
    return render(request, 'users/pw_change_complete.html')


def _clean_next_url(request, username=None):
    if 'next' in request.POST:
        url = request.POST.get('next')
    elif 'next' in request.GET:
        url = request.GET.get('next')
    elif 'HTTP_REFERER' in request.META:
        url = request.META.get('HTTP_REFERER').decode('latin1', 'ignore')
    else:
        return None

    site = Site.objects.get_current()
    if not is_safe_url(url, site.domain):
        return None
    parsed_url = urlparse.urlparse(url)

    # Don't redirect right back to login, logout, register, change email, or
    # edit profile pages
    locale, register_url = split_path(reverse(
        'users.browserid_register'))
    locale, change_email_url = split_path(reverse(
        'users.change_email'))
    locale, edit_profile_url = split_path(reverse(
        'devmo_profile_edit', args=[username, ]))
    REDIRECT_HOME_URLS = [settings.LOGIN_URL, settings.LOGOUT_URL,
                          register_url, change_email_url, edit_profile_url]
    for home_url in REDIRECT_HOME_URLS:
        if home_url in parsed_url.path:
            return None

    # TODO?HACK: can't use urllib.quote_plus because mod_rewrite quotes the
    # next url value already.
    url = url.replace(' ', '+')
    return url


@permission_required('users.add_userban')
def ban_user(request, user_id):
    """
    Ban a user.

    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        form = UserBanForm(data=request.POST)
        if form.is_valid():
            ban = UserBan(user=user,
                          by=request.user,
                          reason=form.cleaned_data['reason'],
                          is_active=True)
            ban.save()
            return HttpResponseRedirect(user.get_absolute_url())
    form = UserBanForm()
    return render(request,
                  'users/ban_user.html',
                  {'form': form,
                   'user': user})

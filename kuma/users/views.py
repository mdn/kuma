import urlparse

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sites.models import Site
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.http import (HttpResponse, HttpResponseRedirect, Http404,
                         HttpResponseForbidden)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters

from django.utils.http import is_safe_url

from django_browserid.forms import BrowserIDForm
from django_browserid.auth import get_audience
from django_browserid import auth as browserid_auth

from access.decorators import login_required
from badger.models import Award
import constance.config
from taggit.utils import parse_tags
from teamwork.models import Team
from waffle import switch_is_active

from demos.models import Submission
from sumo.decorators import ssl_required
from sumo.urlresolvers import reverse, split_path

from .forms import (BrowserIDRegisterForm, UserBanForm,
                    UserProfileEditForm, newsletter_subscribe,
                    get_subscription_details, subscribed_to_newsletter)
from .models import UserProfile, UserBan
from .tasks import send_welcome_email


SESSION_VERIFIED_EMAIL = getattr(settings, 'BROWSERID_SESSION_VERIFIED_EMAIL',
                                 'browserid_verified_email')
SESSION_REDIRECT_TO = getattr(settings, 'BROWSERID_SESSION_REDIRECT_TO',
                              'browserid_redirect_to')
# TODO: Make this dynamic, editable from admin interface
INTEREST_SUGGESTIONS = [
    "audio", "canvas", "css3", "device", "files", "fonts",
    "forms", "geolocation", "javascript", "html5", "indexeddb", "dragndrop",
    "mobile", "offlinesupport", "svg", "video", "webgl", "websockets",
    "webworkers", "xhr", "multitouch",

    "front-end development",
    "web development",
    "tech writing",
    "user experience",
    "design",
    "technical review",
    "editorial review",
]


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
    if users.exists():
        return users[0]
    else:
        return None


def set_browserid_explained(response):
    response.set_cookie('browserid_explained', 1, max_age=31536000)
    return response


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
                  {'register_form': register_form})


@ssl_required
@xframe_options_sameorigin
def login(request):
    """Try to log the user in."""
    next_url = _clean_next_url(request)
    if request.method == 'GET' and request.user.is_authenticated():
        if next_url:
            return redirect(next_url)
    else:
        next_url = _clean_next_url(request) or reverse('home')
    return render(request, 'users/login.html', {'next_url': next_url})


@ssl_required
def logout(request):
    """Log the user out."""
    username = request.user.username

    auth.logout(request)
    next_url = _clean_next_url(request, username) or reverse('home')
    resp = HttpResponseRedirect(next_url)
    return resp


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
    locale, edit_profile_url = split_path(reverse(
        'users.profile_edit', args=[username, ]))
    REDIRECT_HOME_URLS = [settings.LOGIN_URL, settings.LOGOUT_URL,
                          register_url, edit_profile_url]
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


def profile_view(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    user = profile.user

    if (UserBan.objects.filter(user=user, is_active=True) and
            not request.user.is_superuser):
        return render(request, '403.html',
                      {'reason': "bannedprofile"}, status=403)

    DEMOS_PAGE_SIZE = getattr(settings, 'DEMOS_PAGE_SIZE', 12)
    sort_order = request.GET.get('sort', 'created')
    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    show_hidden = (user == request.user) or user.is_superuser

    demos = (Submission.objects.all_sorted(sort_order)
                               .filter(creator=profile.user))
    if not show_hidden:
        demos = demos.exclude(hidden=True)

    demos_paginator = Paginator(demos, DEMOS_PAGE_SIZE, True)
    demos_page = demos_paginator.page(page_number)

    wiki_activity, docs_feed_items = None, None
    wiki_activity = profile.wiki_activity()

    awards = Award.objects.filter(user=user)

    if request.user.is_anonymous():
        show_manage_roles_button = False
    else:
        # TODO: This seems wasteful, just to decide whether to show the button
        roles_by_team = Team.objects.get_team_roles_managed_by(request.user,
                                                               user)
        show_manage_roles_button = (len(roles_by_team) > 0)

    context = {
        'profile': profile,
        'demos': demos,
        'demos_paginator': demos_paginator,
        'demos_page': demos_page,
        'docs_feed_items': docs_feed_items,
        'wiki_activity': wiki_activity,
        'award_list': awards,
        'show_manage_roles_button': show_manage_roles_button,
    }
    return render(request, 'users/profile.html', context)


@login_required
def my_profile(request):
    return redirect(request.user)


def profile_edit(request, username):
    """View and edit user profile"""
    profile = get_object_or_404(UserProfile, user__username=username)
    if not profile.allows_editing_by(request.user):
        return HttpResponseForbidden()

    context = {'profile': profile}

    # Map of form field names to tag namespaces
    field_to_tag_ns = (
        ('interests', 'profile:interest:'),
        ('expertise', 'profile:expertise:')
    )

    if request.method != 'POST':
        initial = dict(email=profile.user.email, beta=profile.beta_tester)

        # Load up initial websites with either user data or required base URL
        for name, meta in UserProfile.website_choices:
            initial['websites_%s' % name] = profile.websites.get(name, '')

        # Form fields to receive tags filtered by namespace.
        for field, ns in field_to_tag_ns:
            initial[field] = ', '.join(t.name.replace(ns, '')
                                       for t in profile.tags.all_ns(ns))

        subscription_details = get_subscription_details(profile.user.email)
        if subscribed_to_newsletter(subscription_details):
            initial['newsletter'] = True
            initial['agree'] = True

        # Finally, set up the forms.
        form = UserProfileEditForm(request.locale,
                                   instance=profile,
                                   initial=initial)

    else:
        form = UserProfileEditForm(request.locale,
                                   request.POST,
                                   request.FILES,
                                   instance=profile)
        if form.is_valid():
            profile_new = form.save(commit=False)

            # Gather up all websites defined by the model, save them.
            sites = dict()
            for name, meta in UserProfile.website_choices:
                field_name = 'websites_%s' % name
                field_value = form.cleaned_data.get(field_name, '')
                if field_value and field_value != meta['prefix']:
                    sites[name] = field_value
            profile_new.websites = sites

            # Save the profile record now, since the rest of this deals with
            # related resources...
            profile_new.save()

            # Update tags from form fields
            for field, tag_ns in field_to_tag_ns:
                tags = [t.lower()
                        for t in parse_tags(form.cleaned_data.get(field, ''))]
                profile_new.tags.set_ns(tag_ns, *tags)

            newsletter_subscribe(request, profile_new.user.email,
                                 form.cleaned_data)
            return redirect(profile.user)
    context['form'] = form
    context['INTEREST_SUGGESTIONS'] = INTEREST_SUGGESTIONS

    return render(request, 'users/profile_edit.html', context)


@login_required
def my_profile_edit(request):
    return redirect('users.profile_edit', request.user.username)

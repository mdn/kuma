import collections
import operator

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect

from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.socialaccount import helpers
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.views import SignupView as BaseSignupView
from constance import config
from honeypot.decorators import verify_honeypot_value
from taggit.utils import parse_tags
from tower import ugettext_lazy as _

from kuma.core.decorators import login_required
from kuma.demos.models import Submission
from kuma.demos.views import DEMOS_PAGE_SIZE

from .forms import UserBanForm, UserProfileEditForm, NewsletterForm
from .models import UserProfile, UserBan
# we have to import the signup form here due to allauth's odd form subclassing
# that requires providing a base form class (see ACCOUNT_SIGNUP_FORM_CLASS)
from .signup import SignupForm


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


@permission_required('users.add_userban')
def ban_user(request, user_id):
    """
    Ban a user.
    """
    User = get_user_model()
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
            return redirect(user)
    form = UserBanForm()
    return render(request,
                  'users/ban_user.html',
                  {'form': form,
                   'user': user})


def profile_view(request, username):
    """
    The main profile view that only collects a bunch of user
    specific data to populate the template context.
    """
    profile = get_object_or_404(UserProfile.objects.select_related('user'),
                                user__username=username)

    if (profile.is_banned and not request.user.is_superuser):
        return render(request, '403.html',
                      {'reason': "bannedprofile"}, status=403)

    sort_order = request.GET.get('sort', 'created')
    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1
    show_hidden = (profile.user == request.user) or profile.user.is_superuser

    demos = (Submission.objects.all_sorted(sort_order)
                               .filter(creator=profile.user))
    if not show_hidden:
        demos = demos.exclude(hidden=True)

    demos_paginator = Paginator(demos, DEMOS_PAGE_SIZE, True)
    demos_page = demos_paginator.page(page_number)

    docs_feed_items = None

    context = {
        'profile': profile,
        'demos': demos,
        'demos_paginator': demos_paginator,
        'demos_page': demos_page,
        'docs_feed_items': docs_feed_items,
    }
    return render(request, 'users/profile.html', context)


@login_required
def my_profile(request):
    return redirect(request.user)


def profile_edit(request, username):
    """
    View and edit user profile
    """
    profile = get_object_or_404(UserProfile, user__username=username)

    if not profile.allows_editing_by(request.user):
        return HttpResponseForbidden()

    # Map of form field names to tag namespaces
    field_to_tag_ns = (
        ('interests', 'profile:interest:'),
        ('expertise', 'profile:expertise:')
    )

    already_subscribed = NewsletterForm.is_subscribed(profile.user.email)

    if request.method != 'POST':
        initial = {
            'beta': profile.beta_tester,
            'username': profile.user.username,
        }
        # Load up initial websites with either user data or required base URL
        for name, meta in UserProfile.website_choices:
            initial['websites_%s' % name] = profile.websites.get(name, '')

        # Form fields to receive tags filtered by namespace.
        for field, ns in field_to_tag_ns:
            initial[field] = ', '.join(t.name.replace(ns, '')
                                       for t in profile.tags.all_ns(ns))

        subscription_initial = {}
        if already_subscribed:
            subscription_initial['newsletter'] = True
            subscription_initial['agree'] = True

        # Finally, set up the forms.
        profile_form = UserProfileEditForm(instance=profile,
                                           initial=initial,
                                           prefix='profile')
        newsletter_form = NewsletterForm(locale=request.locale,
                                         already_subscribed=already_subscribed,
                                         prefix='newsletter',
                                         initial=subscription_initial)
    else:
        profile_form = UserProfileEditForm(data=request.POST,
                                           files=request.FILES,
                                           instance=profile,
                                           prefix='profile')
        newsletter_form = NewsletterForm(locale=request.locale,
                                         already_subscribed=already_subscribed,
                                         data=request.POST,
                                         prefix='newsletter')

        # Don't validate if the username hasn't changed so people
        # can keep already existing invalid usernames.
        posted_username = request.POST.get('profile-username', None)
        if posted_username is not None:
            username_changed = request.user.username != posted_username
        else:
            username_changed = False

        if profile_form.is_valid() and newsletter_form.is_valid():
            if username_changed:
                profile.user.username = profile_form.cleaned_data['username']
                profile.user.save()

            profile_new = profile_form.save(commit=False)

            # Gather up all websites defined by the model, save them.
            sites = {}
            for name, meta in UserProfile.website_choices:
                field_name = 'websites_%s' % name
                field_value = profile_form.cleaned_data.get(field_name, '')
                if field_value and field_value != meta['prefix']:
                    sites[name] = field_value
            profile_new.websites = sites

            # Save the profile record now, since the rest of this deals with
            # related resources...
            profile_new.save()

            try:
                # Beta
                beta_group = Group.objects.get(name=config.BETA_GROUP_NAME)
                if profile_form.cleaned_data['beta']:
                    beta_group.user_set.add(request.user)
                else:
                    beta_group.user_set.remove(request.user)
            except Group.DoesNotExist:
                # If there's no Beta Testers group, ignore that logic
                pass

            # Update tags from form fields
            for field, tag_ns in field_to_tag_ns:
                tags = [t.lower()
                        for t in parse_tags(profile_form.cleaned_data.get(field, ''))]
                profile_new.tags.set_ns(tag_ns, *tags)

            newsletter_form.subscribe(request, profile_new.user.email)
            return redirect(profile.user)

    context = {
        'profile': profile,
        'profile_form': profile_form,
        'newsletter_form': newsletter_form,
        'INTEREST_SUGGESTIONS': INTEREST_SUGGESTIONS,
    }
    return render(request, 'users/profile_edit.html', context)


@login_required
def my_profile_edit(request):
    return redirect('users.profile_edit', request.user.username)


def apps_newsletter(request):
    """
    Just a placeholder for an old view that we used to have to handle
    newsletter subscriptions before they were moved into the user profile
    edit view.
    """
    return render(request, 'users/apps_newsletter.html', {})


class SignupView(BaseSignupView):
    """
    The default signup view from the allauth account app, only to
    additionally pass in the locale to the SignupForm as defined in
    the ACCOUNT_SIGNUP_FORM_CLASS setting. This is needed to correctly
    populate the country form field's choices from the product_details
    app.

    You can remove this class if there is no other modification compared
    to it's parent class.
    """
    form_class = SignupForm

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        self.email_addresses = collections.OrderedDict()
        form = super(SignupView, self).get_form(form_class)
        form.fields['email'].label = _('Email address')
        self.matching_user = None
        initial_username = form.initial.get('username', None)
        # For GitHub users, see if we can find matching user by username
        if self.sociallogin.account.provider == 'github':
            User = get_user_model()
            try:
                self.matching_user = User.objects.get(username=initial_username)
                # deleting the initial username because we found a matching user
                del form.initial['username']
            except User.DoesNotExist:
                pass

        email = self.sociallogin.account.extra_data.get('email') or None

        # For Persona users, see if we can find matching user by email address
        if self.sociallogin.account.provider == 'persona':
            try:
                matching_addresses = EmailAddress.objects.filter(email=email,
                                                                 verified=True)
                matching_emailaddress = matching_addresses[0]
                self.matching_user = matching_emailaddress.user
                email_address = {'email': email,
                                 'verified': matching_emailaddress.verified,
                                 'primary': matching_emailaddress.primary}
                self.email_addresses[email] = email_address
            except IndexError:
                pass

        extra_email_addresses = (self.sociallogin
                                     .account
                                     .extra_data
                                     .get('email_addresses', None))

        # if we didn't get any extra email addresses from the provider
        # but the default email is available, simply hide the form widget
        if extra_email_addresses is None and email is not None:
            form.fields['email'].widget = forms.HiddenInput()

        # if there are extra email addresses from the provider (like GitHub)
        elif extra_email_addresses is not None:
            # build a mapping of the email addresses to their other values
            # to be used later for resetting the social accounts email addresses
            for email_address in extra_email_addresses:
                self.email_addresses[email_address['email']] = email_address

            # build the choice list with the given email addresses
            # if there is a main email address offer that as well (unless it's
            # already there)
            if email is not None and email not in self.email_addresses:
                self.email_addresses[email] = {
                    'email': email,
                    'verified': False,
                    'primary': False,
                }
            choices = []
            verified_emails = []
            for email_address in self.email_addresses.values():
                if email_address['verified']:
                    label = _('%(email)s <b>Verified</b>')
                    verified_emails.append(email_address['email'])
                else:
                    label = _('%(email)s Unverified')
                next_email = email_address['email']
                choices.append((next_email, label % {'email': next_email}))
            choices.append((form.other_email_value, _('Other:')))
            email_select = forms.RadioSelect(choices=choices,
                                             attrs={'id': 'email'})
            form.fields['email'].widget = email_select
            if not email and len(verified_emails) == 1:
                form.initial.update(email=verified_emails[0])
        return form

    def get_form_kwargs(self):
        kwargs = super(SignupView, self).get_form_kwargs()
        kwargs.update({
            'locale': self.request.locale,
            'already_subscribed': False,
        })
        return kwargs

    def form_valid(self, form):
        """
        We use the selected email here and reset the social loging list of
        email addresses before they get created.

        We send our welcome email via celery during complete_signup.
        So, we need to manually commit the user to the db for it.
        """
        selected_email = form.cleaned_data['email']
        if form.other_email_used:
            email_address = {
                'email': selected_email,
                'verified': False,
                'primary': True,
            }
        else:
            email_address = self.email_addresses.get(selected_email, None)

        if email_address:
            email_address['primary'] = True
            primary_email_address = EmailAddress(**email_address)
            form.sociallogin.email_addresses = \
                self.sociallogin.email_addresses = [primary_email_address]
            if email_address['verified']:
                # we have to stash the selected email address here
                # so that no email verification is sent again
                # this is done by adding the email address to the session
                get_adapter().stash_verified_email(self.request,
                                                   email_address['email'])

        with transaction.atomic():
            form.save(self.request)
        return helpers.complete_social_signup(self.request,
                                              self.sociallogin)

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        or_query = []
        # For GitHub users, find matching Persona social accounts by emails
        if self.sociallogin.account.provider == 'github':
            for email_address in self.email_addresses.values():
                if email_address['verified']:
                    or_query.append(Q(uid=email_address['email']))

        # For Persona users, find matching GitHub social accounts directly
        elif self.sociallogin.account.provider == 'persona':
            if self.matching_user:
                or_query.append(Q(user=self.matching_user, provider='github'))

        if or_query:
            reduced_or_query = reduce(operator.or_, or_query)
            matching_accounts = (SocialAccount.objects
                                              .filter(reduced_or_query))
        else:
            matching_accounts = SocialAccount.objects.none()
        context.update({
            'email_addresses': self.email_addresses,
            'matching_user': self.matching_user,
            'matching_accounts': matching_accounts,
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        response = verify_honeypot_value(request, None)
        if isinstance(response, HttpResponseBadRequest):
            return response
        return super(SignupView, self).dispatch(request, *args, **kwargs)


signup = SignupView.as_view()

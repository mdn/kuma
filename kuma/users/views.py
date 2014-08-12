from django import forms
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.datastructures import SortedDict

from access.decorators import login_required
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.socialaccount.views import SignupView as BaseSignupView
from allauth.socialaccount import helpers
from badger.models import Award
import constance.config
from taggit.utils import parse_tags
from teamwork.models import Team
from tower import ugettext_lazy as _

from kuma.demos.models import Submission
from kuma.demos.views import DEMOS_PAGE_SIZE

from .forms import (UserBanForm, UserProfileEditForm, NewsletterForm,
                    get_subscription_details, subscribed_to_newsletter,
                    newsletter_subscribe)
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
    profile = get_object_or_404(UserProfile, user__username=username)
    user = profile.user

    if (user.bans.filter(is_active=True).exists() and
            not request.user.is_superuser):
        return render(request, '403.html',
                      {'reason': "bannedprofile"}, status=403)

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

    if request.method != 'POST':
        initial = {
            'beta': profile.beta_tester,
        }
        # Load up initial websites with either user data or required base URL
        for name, meta in UserProfile.website_choices:
            initial['websites_%s' % name] = profile.websites.get(name, '')

        # Form fields to receive tags filtered by namespace.
        for field, ns in field_to_tag_ns:
            initial[field] = ', '.join(t.name.replace(ns, '')
                                       for t in profile.tags.all_ns(ns))

        subscription_details = get_subscription_details(profile.user.email)
        subscription_initial = {}
        if subscribed_to_newsletter(subscription_details):
            subscription_initial['newsletter'] = True
            subscription_initial['agree'] = True

        # Finally, set up the forms.
        profile_form = UserProfileEditForm(instance=profile,
                                           initial=initial,
                                           prefix='profile')
        newsletter_form = NewsletterForm(request.locale,
                                         prefix='newsletter',
                                         initial=subscription_initial)
    else:
        profile_form = UserProfileEditForm(data=request.POST,
                                           files=request.FILES,
                                           instance=profile,
                                           prefix='profile')
        newsletter_form = NewsletterForm(request.locale,
                                         data=request.POST,
                                         prefix='newsletter')

        if profile_form.is_valid() and newsletter_form.is_valid():
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
                beta_group = Group.objects.get(name=constance.config.BETA_GROUP_NAME)
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

            newsletter_subscribe(request, profile_new.user.email,
                                 newsletter_form.cleaned_data)
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
        self.email_addresses = SortedDict()
        form = super(SignupView, self).get_form(form_class)
        form.fields['email'].label = _('Email address')

        email = self.sociallogin.account.extra_data.get('email') or None
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
            for email_address in self.email_addresses.values():
                if email_address['verified']:
                    label = _('%(email)s <b>Verified</b>')
                else:
                    label = _('%(email)s Unverified')
                email = email_address['email']
                choices.append((email, label % {'email': email}))
            choices.append((form.other_email_value, _('other:')))
            email_select = forms.RadioSelect(choices=choices,
                                             attrs={'id': 'email'})
            form.fields['email'].widget = email_select
        return form

    def get_form_kwargs(self):
        kwargs = super(SignupView, self).get_form_kwargs()
        kwargs['locale'] = self.request.locale
        return kwargs

    def form_valid(self, form):
        """
        We use the selected email here and reset the social loging list of
        email addresses before they get created.

        We send our welcome email via celery during complete_signup.
        So, we need to manually commit the user to the db for it.
        """
        selected_email = form.cleaned_data['email']
        if selected_email == form.other_email_value:
            email_address = {
                'email': form.cleaned_data['other_email'],
                'verified': False,
                'primary': True,
            }
        else:
            email_address = self.email_addresses.get(selected_email, None)
        if email_address:
            email_address['primary'] = True
            self.sociallogin.email_addresses = [EmailAddress(*email_address)]
            if email_address['verified']:
                # we have to stash the selected email address here
                # so that no email verification is sent again
                # this is done by adding the email address to the session
                get_adapter().stash_verified_email(self.request,
                                                   email_address['email'])

        with transaction.commit_on_success():
            form.save(self.request)
        return helpers.complete_social_signup(self.request,
                                              self.sociallogin)

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        context.update({
            'email_addresses': self.email_addresses,
        })
        return context


signup = SignupView.as_view()

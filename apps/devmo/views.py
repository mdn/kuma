from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.http import (HttpResponseRedirect, HttpResponseForbidden)

from devmo.urlresolvers import reverse

import constance.config
import basket
from taggit.utils import parse_tags
from waffle import flag_is_active

from waffle import flag_is_active

from access.decorators import login_required
from demos.models import Submission
from teamwork.models import Team
from badger.models import Award
from users.models import UserBan

from . import INTEREST_SUGGESTIONS
from .models import Calendar, Event, UserProfile
from .forms import (UserProfileEditForm, newsletter_subscribe,
                    get_subscription_details, subscribed_to_newsletter)


DOCS_ACTIVITY_MAX_ITEMS = getattr(settings,
        'DOCS_ACTIVITY_MAX_ITEMS', 15)


def events(request):
    """Developer Engagement Calendar"""
    cal = Calendar.objects.get(shortname='devengage_events')
    events = Event.objects.filter(calendar=cal)
    upcoming_events = events.filter(done=False)
    past_events = events.filter(done=True)
    google_maps_api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY',
        "ABQIAAAAijZqBZcz-rowoXZC1tt9iRT5rHVQFKUGOHoyfP"
        "_4KyrflbHKcRTt9kQJVST5oKMRj8vKTQS2b7oNjQ")

    return render(request, 'devmo/calendar.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'google_maps_api_key': google_maps_api_key
    })


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

    demos = Submission.objects.all_sorted(sort_order).filter(
                                                        creator=profile.user)
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

    template = 'devmo/profile.html'

    return render(request, template, dict(
        profile=profile, demos=demos, demos_paginator=demos_paginator,
        demos_page=demos_page, docs_feed_items=docs_feed_items,
        wiki_activity=wiki_activity, award_list=awards,
        show_manage_roles_button=show_manage_roles_button,
    ))


@login_required
def my_profile(request):
    user = request.user
    return HttpResponseRedirect(reverse(
            'devmo.views.profile_view', args=(user.username,)))


def profile_edit(request, username):
    """View and edit user profile"""
    profile = get_object_or_404(UserProfile, user__username=username)
    context = {'profile': profile}
    if not profile.allows_editing_by(request.user):
        return HttpResponseForbidden()

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
                tags = [t.lower() for t in parse_tags(
                                            form.cleaned_data.get(field, ''))]
                profile_new.tags.set_ns(tag_ns, *tags)

            newsletter_subscribe(request, profile_new.user.email,
                                 form.cleaned_data)
            return HttpResponseRedirect(reverse(
                    'devmo.views.profile_view', args=(profile.user.username,)))
    context['form'] = form
    context['INTEREST_SUGGESTIONS'] = INTEREST_SUGGESTIONS

    return render(request, 'devmo/profile_edit.html', context)


@login_required
def my_profile_edit(request):
    user = request.user
    return HttpResponseRedirect(reverse(
            'devmo.views.profile_edit', args=(user.username,)))

import jingo
import urllib2
import csv
import logging

from django.shortcuts import get_object_or_404
from django.http import (HttpResponseRedirect, HttpResponse,
                         HttpResponseForbidden, HttpResponseNotFound)

from devmo.urlresolvers import reverse

from taggit.utils import parse_tags, edit_string_for_tags

from . import INTEREST_SUGGESTIONS
from .models import Calendar, Event, UserProfile
from .forms import UserProfileEditForm


def events(request):
    """Developer Engagement Calendar"""
    cal = Calendar.objects.get(shortname='devengage_events')
    events = Event.objects.filter(calendar=cal)
    upcoming_events = events.filter(done=False)
    past_events = events.filter(done=True)

    return jingo.render(request, 'devmo/calendar.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events
    })


def profile_view(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    return jingo.render(request, 'devmo/profile.html', dict(
        profile=profile
    ))


def profile_edit(request, username):
    """View and edit user profile"""
    profile = get_object_or_404(UserProfile, user__username=username)
    if not profile.allows_editing_by(request.user):
        return HttpResponseForbidden()

    if request.method != "POST":

        initial = dict(email=profile.user.email)

        # Load up initial websites with either user data or required base URL
        for name, meta in UserProfile.website_choices:
            val = profile.websites.get(name, '') or meta['prefix']
            initial['websites_%s' % name] = val

        # Form fields to receive tags filtered by prefix.
        tags_accum = {
            ('interests', 'profile:interest:'): [],
            ('expert_in', 'profile:expert:'): []
        }

        # Collect the prefixed tags, sans prefix.
        for t in profile.tags.all():
            for k, v in tags_accum.items():
                if t.name.startswith(k[1]):
                    tags_accum[k].append(t.name.replace(k[1], ''))

        # Build the initial form values based on tags.
        for k, v in tags_accum.items():
            initial[k[0]] = ', '.join(v)

        # Finally, set up the form.
        form = UserProfileEditForm(instance=profile, initial=initial)

    else:
        form = UserProfileEditForm(request.POST, request.FILES,
                                   instance=profile)
        if form.is_valid():
            profile_new = form.save(commit=False)

            # Gather up all websites defined by the model, save them.
            sites = dict()
            for name, meta in UserProfile.website_choices:
                field_name = 'websites_%s' % name
                field_value = form.cleaned_data.get(field_name, '')
                if field_value:
                    sites[name] = field_value
            profile_new.websites = sites

            # Save the profile record now, since the rest of this deals with
            # related resources...
            profile_new.save()

            # Selectively edit the profile:interest: and profile:expert: tags
            # for the profile.
            orig_tags = profile_new.tags.all()
            new_tags = [t.name for t in orig_tags
                        if not t.name.startswith('profile:interest:')
                        and not t.name.startswith('profile:expert:')]
            new_tags.extend('profile:interest:%s' % t for t in
                parse_tags(form.cleaned_data.get('interests', '')))
            new_tags.extend('profile:expert:%s' % t for t in
                parse_tags(form.cleaned_data.get('expert_in', '')))
            profile_new.tags.set(*new_tags)

            # Change the email address, if necessary.
            if form.cleaned_data['email'] != profile.user.email:
                profile.user.email = form.cleaned_data['email']
                profile.user.save()
                profile.deki_user.change_email(form.cleaned_data['email'])

            return HttpResponseRedirect(reverse(
                    'devmo.views.profile_view', args=(profile.user.username,)))

    return jingo.render(request, 'devmo/profile_edit.html', dict(
        profile=profile, form=form, INTEREST_SUGGESTIONS=INTEREST_SUGGESTIONS
    ))

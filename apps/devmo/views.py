import jingo
import urllib2
import csv
import logging

from django.shortcuts import get_object_or_404
from django.http import (HttpResponseRedirect, HttpResponse,
                         HttpResponseForbidden, HttpResponseNotFound)

from devmo.urlresolvers import reverse

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
        for name, meta in UserProfile.website_choices:
            val = profile.websites.get(name, '') or meta['prefix']
            initial['websites_%s' % name] = val
        form = UserProfileEditForm(instance=profile, initial=initial)

    else:
        form = UserProfileEditForm(request.POST, request.FILES,
                                   instance=profile,
                                   initial=dict(email=profile.user.email))
        if form.is_valid():
            profile_new = form.save(commit=False)

            # Gather up all websites defined by the model, save them.
            sites = dict()
            for name, meta in profile.website_choices:
                field_name = 'websites_%s' % name
                field_value = form.cleaned_data.get(field_name, '')
                if field_value:
                    sites[name] = field_value
            profile_new.websites = sites

            profile_new.save()

            # Change the email address, if necessary.
            if form.cleaned_data['email'] != profile.user.email:
                profile.user.email = form.cleaned_data['email']
                profile.user.save()
                profile.deki_user.change_email(form.cleaned_data['email'])

            return HttpResponseRedirect(reverse(
                    'devmo.views.profile_view', args=(profile.user.username,)))

    return jingo.render(request, 'devmo/profile_edit.html', dict(
        profile=profile, form=form
    ))

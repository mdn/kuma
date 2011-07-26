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
        form = UserProfileEditForm(instance=profile,
                                   initial=dict(email=profile.user.email))
    else:
        form = UserProfileEditForm(request.POST, request.FILES,
                                   instance=profile,
                                   initial=dict(email=profile.user.email))
        if form.is_valid():
            profile_new = form.save(commit=False)
            profile_new.save()

            if form.cleaned_data['email'] != profile.user.email:
                profile.user.email = form.cleaned_data['email']
                profile.user.save()
                profile.deki_user.change_email(form.cleaned_data['email'])

            return HttpResponseRedirect(reverse(
                    'devmo.views.profile_view', args=(profile.user.username,)))

    return jingo.render(request, 'devmo/profile_edit.html', dict(
        profile=profile, form=form
    ))

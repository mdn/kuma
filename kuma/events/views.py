from django.conf import settings
from django.shortcuts import render

from .models import Event

GOOGLE_MAPS_API_KEY = getattr(settings, 'GOOGLE_MAPS_API_KEY',
    "ABQIAAAAijZqBZcz-rowoXZC1tt9iRT5rHVQFKUGOHoyfP"
    "_4KyrflbHKcRTt9kQJVST5oKMRj8vKTQS2b7oNjQ")


def events(request):
    """Developer Engagement Calendar"""
    events = Event.objects.filter(calendar__shortname='devengage_events')
    upcoming_events = events.filter(done=False)
    past_events = events.filter(done=True)

    return render(request, 'events/calendar.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'google_maps_api_key': GOOGLE_MAPS_API_KEY
    })

import jingo
import urllib2
import csv

from devmo.models import Calendar, Event

def as_unicode(events):
    for row in events:
        for idx, cell in enumerate(row):
            row[idx] = unicode(cell, 'utf-8')
        yield row

def calendar(request):
    """Developer Engagement Calendar"""
    u = urllib2.urlopen('https://spreadsheets.google.com/pub?key=0AhphLklK1Ve4dGo5UGpIcG80Rm5wZ1BiTXNTQ2RWaUE&output=csv')
    events = list(as_unicode(csv.reader(u)))
    upcoming_events = []
    past_events = []
    for event in events[1:]:
        if len(event) > 7:
            if event[7] == 'no':
                upcoming_events.append(event)
            elif event[7] == 'yes':
                past_events.append(event)

    # populate fieldnames list
    return jingo.render(request, 'devmo/calendar.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events
    })

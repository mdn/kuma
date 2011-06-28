import cronjobs

from devmo.models import Calendar


@cronjobs.register
def devmo_calendar_reload():
    calendar = Calendar.objects.get(shortname='devengage_events')
    calendar.reload()

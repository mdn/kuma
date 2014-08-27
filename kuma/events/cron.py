import cronjobs

from .models import Calendar


@cronjobs.register
def calendar_reload():
    calendar = Calendar.objects.get(shortname='devengage_events')
    calendar.reload()

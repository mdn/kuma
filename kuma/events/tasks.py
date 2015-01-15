from celery.task import task

from .models import Calendar


@task
def calendar_reload():
    calendar = Calendar.objects.get(shortname='devengage_events')
    calendar.reload()

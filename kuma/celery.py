import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kuma.settings.local")

app = Celery("kuma")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


@app.task()
def debug_task_returning(a, b):
    """Useful to see if the results backend is working.
    And it also checks that called with a `datetime.date`
    it gets that as parameters in the task."""
    import datetime

    assert isinstance(a, datetime.date), type(a)
    assert isinstance(b, datetime.date), type(b)
    return a < b

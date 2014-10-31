from celery.task import task

from django.db.models import get_model


@task(name="c.unittest.SomeAppTask")
def SomeAppTask(**kwargs):
    return 42


@task(name="c.unittest.SomeModelTask")
def SomeModelTask(pk):
    model = get_model("someapp", "Thing")
    thing = model.objects.get(pk=pk)
    return thing.name

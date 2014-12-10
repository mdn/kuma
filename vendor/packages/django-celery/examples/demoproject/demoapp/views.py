# Create your views here.

from django.http import HttpResponse

from demoapp import tasks


def foo(request):
    r = tasks.add.delay(2, 2)
    return HttpResponse(r.task_id)

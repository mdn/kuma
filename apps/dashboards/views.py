from django.http import HttpResponse


def home(request):
    return HttpResponse('Hi, welcome home!')

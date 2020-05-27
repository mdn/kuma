import logging

from django.shortcuts import render

log = logging.getLogger("kuma.preferences.views")


def index(request):
    return render(request, "preferences/index.html")

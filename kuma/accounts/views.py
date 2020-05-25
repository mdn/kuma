import logging

from django.shortcuts import render

from kuma.core.decorators import login_required

log = logging.getLogger("kuma.accounts.views")


@login_required
def index(request):
    return render(request, "accounts/index.html")

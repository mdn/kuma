import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from waffle.decorators import waffle_flag

from kuma.users.models import User


log = logging.getLogger("kuma.payments.views")


@never_cache
def index(request):
    if not settings.ENABLE_SUBSCRIPTIONS:
        raise Http404("Not enabled")
    highest_subscriber_number = User.get_highest_subscriber_number()
    context = {"next_subscriber_number": highest_subscriber_number + 1}
    return render(request, "payments/index.html", context)


@waffle_flag("subscription")
@never_cache
def thank_you(request):
    return render(request, "payments/thank-you.html")


@waffle_flag("subscription")
@never_cache
def payment_terms(request):
    return render(request, "payments/terms.html")


@waffle_flag("subscription")
@never_cache
def payment_management(request):
    return render(request, "payments/management.html")

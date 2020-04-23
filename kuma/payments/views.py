import logging

from django.shortcuts import render
from django.views.decorators.cache import never_cache
from waffle.decorators import waffle_flag

from kuma.core.decorators import login_required
from kuma.users.models import User


log = logging.getLogger("kuma.payments.views")


@never_cache
def index(request):
    highest_subscriber_number = User.get_highest_subscriber_number()
    # TODO: This is never unit tested because our tests never test SSR rendering.
    # See https://github.com/mdn/kuma/issues/6797
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
@login_required
@never_cache
def payment_management(request):
    return render(request, "payments/management.html")

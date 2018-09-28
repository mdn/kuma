# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from .forms import ContributionForm
from .tasks import contribute_thank_you_email
from .utils import enabled


def skip_if_disabled(func):
    """If contributions are not enabled, then 404."""
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        if enabled(request):
            return func(request, *args, **kwargs)
        raise Http404

    return wrapped


@skip_if_disabled
@never_cache
@csrf_exempt
def contribute(request):
    initial_data = {}
    if request.user.is_authenticated and request.user.email:
        initial_data = {'email': request.user.email}

    if request.POST:
        form = ContributionForm(request.POST)
        if form.is_valid():
            if form.make_charge():
                if settings.MDN_CONTRIBUTION_CONFIRMATION_EMAIL:
                    contribute_thank_you_email.delay(
                        form.cleaned_data['name'],
                        form.cleaned_data['email']
                    )
                return redirect('contribute_succeeded')
            return redirect('contribute_error')

        form = ContributionForm(request.POST)
    else:
        form = ContributionForm(initial=initial_data)

    context = {
        'form': form,
        'hide_cta': True,
    }
    return render(request, 'contributions/contribute.html', context)


@skip_if_disabled
@never_cache
def confirmation(request, status):
    context = {'status': status}
    return render(request, 'contributions/thank_you.html', context)

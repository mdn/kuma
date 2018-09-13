# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from .forms import ContributionForm
from .tasks import contribute_thank_you_email


def skip_if_disabled(func):
    """If not MDN_CONTRIBUTIONS, then 404."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not settings.MDN_CONTRIBUTION:
            raise Http404
        return func(*args, **kwargs)

    return wrapped


@skip_if_disabled
@never_cache
def contribute(request):
    initial_data = {}
    if request.user.is_authenticated and request.user.email:
        initial_data = {'email': request.user.email}

    if request.POST:
        form = ContributionForm(request.POST)
        if form.is_valid():
            charge = form.make_charge()
            if charge and charge.id and charge.status == 'succeeded':
                if settings.MDN_CONTRIBUTION_CONFIRMATION_EMAIL:
                    contribute_thank_you_email.delay(
                        form.cleaned_data['name'],
                        form.cleaned_data['email']
                    )
                return redirect('contribute_confirmation_succeeded')
            return redirect('contribute_confirmation_error')

        form = ContributionForm(request.POST)
    else:
        form = ContributionForm(initial=initial_data)

    context = {
        'form': form,
    }
    return render(request, 'contributions/contribute.html', context)


@skip_if_disabled
@never_cache
def contribute_confirmation(request, status):
    context = {'status': status}
    return render(request, 'contributions/thank_you.html', context)

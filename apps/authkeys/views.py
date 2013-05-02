import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.http import (HttpResponseRedirect, HttpResponseForbidden)
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from sumo.utils import paginate, smart_int

from .models import Key
from .forms import KeyForm


ITEMS_PER_PAGE = 15


@login_required
def new(request):
    data = {"key": None}
    if request.method != "POST":
        data['form'] = KeyForm()
    else:
        data['form'] = KeyForm(request.POST)
        if data['form'].is_valid():
            new_key = data['form'].save(commit=False)
            new_key.user = request.user
            data['secret'] = new_key.generate_secret()
            new_key.save()
            data['key'] = new_key

    return render(request, 'authkeys/new.html', data)


@login_required
def list(request):
    keys = Key.objects.filter(user=request.user)
    return render(request, 'authkeys/list.html', dict(keys=keys))


@login_required
def history(request, pk):
    key = get_object_or_404(Key, pk=pk)
    if key.user != request.user:
        raise PermissionDenied
    items = key.history.all().order_by('-pk')
    items = paginate(request, items, per_page=ITEMS_PER_PAGE)
    return render(request, 'authkeys/history.html',
                        dict(key=key, items=items))


@login_required
def delete(request, pk):
    key = get_object_or_404(Key, pk=pk)
    if key.user != request.user:
        raise PermissionDenied
    if request.method == "POST":
        key.delete()
        return HttpResponseRedirect(reverse('authkeys.list'))
    return render(request, 'authkeys/delete.html', dict(key=key))

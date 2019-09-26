from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from kuma.core.decorators import ensure_wiki_domain
from kuma.core.utils import paginate

from .forms import KeyForm
from .models import Key


ITEMS_PER_PAGE = 15


@ensure_wiki_domain
@login_required
@permission_required('authkeys.add_key', raise_exception=True)
def new(request):
    context = {"key": None}
    if request.method != "POST":
        context['form'] = KeyForm()
    else:
        context['form'] = KeyForm(request.POST)
        if context['form'].is_valid():
            new_key = context['form'].save(commit=False)
            new_key.user = request.user
            context['secret'] = new_key.generate_secret()
            new_key.save()
            context['key'] = new_key

    return render(request, 'authkeys/new.html', context)


@ensure_wiki_domain
@login_required
def list(request):
    keys = Key.objects.filter(user=request.user)
    return render(request, 'authkeys/list.html', dict(keys=keys))


@ensure_wiki_domain
@login_required
def history(request, pk):
    key = get_object_or_404(Key, pk=pk)
    if key.user != request.user:
        raise PermissionDenied
    items = key.history.all().order_by('-pk')
    items = paginate(request, items, per_page=ITEMS_PER_PAGE)
    context = {
        'key': key,
        'items': items,
    }
    return render(request, 'authkeys/history.html', context)


@ensure_wiki_domain
@login_required
@permission_required('authkeys.delete_key', raise_exception=True)
def delete(request, pk):
    key = get_object_or_404(Key, pk=pk)
    if key.user != request.user:
        raise PermissionDenied
    if request.method == "POST":
        key.delete()
        return redirect('authkeys.list')
    return render(request, 'authkeys/delete.html', {'key': key})

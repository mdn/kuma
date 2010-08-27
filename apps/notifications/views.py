from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

import jingo

from sumo.urlresolvers import reverse
from .models import EventWatch


def remove(request, key):
    """Verify and remove an EventWatch."""
    email = request.GET.get('email')
    ew = get_object_or_404(EventWatch, hash=key, email=email)

    try:
        obj = ew.content_type.get_object_for_this_type(pk=ew.watch_id)
    except ObjectDoesNotExist:
        raise Http404

    if request.method == 'POST':
        ew.delete()
        url_ = reverse('notifications.removed')
        return HttpResponseRedirect(url_)

    return jingo.render(request, 'notifications/remove.html',
                        {'watched': obj, 'watch': ew})


def removed(request):
    """Show a confirmation page after an EventWatch has been removed."""

    return jingo.render(request, 'notifications/gone.html')

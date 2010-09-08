from django.shortcuts import get_object_or_404
from django.http import Http404

import jingo

from sumo.utils import paginate
from .models import Image, Video
import gallery as constants


def gallery(request, filter='images'):
    """The media gallery.

    Filter can be set to 'images' or 'videos'.

    """
    locale = request.GET.get('locale', request.locale)

    if filter == 'images':
        media_qs = Image.objects.filter(locale=locale)
    else:
        media_qs = Video.objects.filter(locale=locale)
    media = paginate(request, media_qs, per_page=constants.ITEMS_PER_PAGE)

    return jingo.render(request, 'gallery/gallery.html',
                        {'media': media,
                         'filter': filter,
                         'locale': locale})


def media(request, media_id, media_type):
    """The media page."""
    if media_type == 'image':
        media = get_object_or_404(Image, pk=media_id)
    elif media_type == 'video':
        media = get_object_or_404(Video, pk=media_id)
    else:
        raise Http404

    return jingo.render(request, 'gallery/media.html',
                        {'media': media,
                         'media_type': media_type})

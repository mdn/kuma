import imghdr
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseBadRequest, Http404)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from commonware.decorators import xframe_sameorigin
import jingo
from tower import ugettext as _

from gallery import ITEMS_PER_PAGE
from gallery.forms import ImageForm, VideoForm
from gallery.models import Image, Video
from gallery.utils import upload_image, upload_video
from sumo.urlresolvers import reverse
from sumo.utils import paginate
from upload.utils import FileTooLargeError

MSG_FAIL_UPLOAD = {'image': _('Could not upload your image.'),
                   'video': _('Could not upload your video.')}


def gallery(request, media_type='image'):
    """The media gallery.

    Filter can be set to 'images' or 'videos'.

    """
    if media_type == 'image':
        media_qs = Image.objects.filter(locale=request.locale)
    elif media_type == 'video':
        media_qs = Video.objects.filter(locale=request.locale)
    else:
        raise Http404

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    draft = _get_draft_info(request.user)
    image_form, video_form = _init_upload_forms(request, draft)

    return jingo.render(request, 'gallery/gallery.html',
                        {'media': media,
                         'media_type': media_type,
                         'image_form': image_form,
                         'video_form': video_form})


def _get_draft_info(user):
    """Get video and image drafts for a given user."""
    draft = {'image': None, 'video': None}
    if user.is_authenticated():
        title = u'draft %s' % user.pk
        draft['image'] = Image.objects.filter(
            creator=user, title=title, locale=settings.WIKI_DEFAULT_LANGUAGE)
        draft['image'] = draft['image'][0] if draft['image'] else None
        draft['video'] = Video.objects.filter(
            creator=user, title=title, locale=settings.WIKI_DEFAULT_LANGUAGE)
        draft['video'] = draft['video'][0] if draft['video'] else None
    return draft


def _init_upload_forms(request, draft):
    """Initialize video and image upload forms given the request and drafts."""
    if draft['image']:
        file = (draft['image'].thumbnail if draft['image'].thumbnail
                                         else draft['image'].file)
        form_data = request.POST.copy()
        form_data['locale'] = draft['image'].locale
        image_form = ImageForm(form_data, {'file': file})
    else:
        image_form = ImageForm()

    if draft['video']:
        file_data = {'flv': draft['video'].flv, 'ogv': draft['video'].ogv,
                     'webm': draft['video'].webm}
        form_data = request.POST.copy()
        form_data['locale'] = draft['video'].locale
        video_form = VideoForm(form_data, file_data)
    else:
        video_form = VideoForm()

    return (image_form, video_form)


@login_required
@require_POST
def upload(request, media_type='image'):
    draft = _get_draft_info(request.user)
    if media_type == 'image' and draft['image']:
        # We're publishing an image draft!
        image_form = ImageForm(request.POST, request.FILES,
                               initial={'file': draft['image'].file})
        if image_form.is_valid():
            draft['image'].title = request.POST.get('title')
            draft['image'].description = request.POST.get('description')
            draft['image'].locale = request.POST.get('locale')
            draft['image'].save()
            return HttpResponseRedirect(draft['image'].get_absolute_url())
        else:
            return gallery(request, media_type='image')
    elif media_type == 'video' and draft['video']:
        # We're publishing a video draft!
        video_form = VideoForm(request.POST, request.FILES,
                               initial={'flv': draft['video'].flv,
                                        'ogv': draft['video'].ogv,
                                        'webm': draft['video'].webm})
        if video_form.is_valid():
            draft['video'].title = request.POST.get('title')
            draft['video'].description = request.POST.get('description')
            draft['video'].locale = request.POST.get('locale')
            draft['video'].save()
            return HttpResponseRedirect(draft['video'].get_absolute_url())
        else:
            return gallery(request, media_type='video')

    return HttpResponseBadRequest(u'Unrecognized POST request.')


@login_required
@require_POST
def cancel_draft(request, media_type='image'):
    """Delete an existing draft for the user."""
    draft = _get_draft_info(request.user)
    if media_type == 'image' and draft['image']:
        draft['image'].delete()
        draft['image'] = None
    elif media_type == 'video' and draft['video']:
        delete_file = request.GET.get('field')
        if delete_file not in ('flv', 'ogv', 'webm'):
            delete_file = None

        if delete_file and getattr(draft['video'], delete_file):
            getattr(draft['video'], delete_file).delete()
        elif not delete_file:
            draft['video'].delete()
            draft['video'] = None
    else:
        return HttpResponseBadRequest(
            u'Unrecognized request or nothing to cancel.')
    return HttpResponseRedirect(reverse('gallery.gallery', args=[media_type]))


def gallery_async(request):
    """AJAX endpoint to media gallery.

    Returns an HTML list representation of the media.

    """
    # Maybe refactor this into existing views and check request.is_ajax?
    media_type = request.GET.get('type', 'image')
    term = request.GET.get('q')
    if media_type == 'image':
        media_qs = Image.objects
    elif media_type == 'video':
        media_qs = Video.objects
    else:
        raise Http404

    if request.locale == settings.WIKI_DEFAULT_LANGUAGE:
        media_qs = media_qs.filter(locale=request.locale)
    else:
        locales = [request.locale, settings.WIKI_DEFAULT_LANGUAGE]
        media_qs = media_qs.filter(locale__in=locales)

    if term:
        media_qs = media_qs.filter(Q(title__icontains=term) |
                                   Q(description__icontains=term))

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return jingo.render(request, 'gallery/includes/media_list.html',
                        {'media_list': media})


def search(request, media_type):
    """Search the media gallery."""

    term = request.GET.get('q')
    if not term:
        url = reverse('gallery.gallery', args=[media_type])
        return HttpResponseRedirect(url)

    filter = Q(title__icontains=term) | Q(description__icontains=term)

    if media_type == 'image':
        media_qs = Image.objects.filter(filter, locale=request.locale)
    elif media_type == 'video':
        media_qs = Video.objects.filter(filter, locale=request.locale)
    else:
        raise Http404

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return jingo.render(request, 'gallery/search.html',
                        {'media': media,
                         'media_type': media_type,
                         'q': term})


@login_required
@require_POST
def delete_media(request, media_id, media_type='image'):
    """Delete media and redirect to gallery view."""
    media, _ = _get_media_info(media_id, media_type)
    media.delete()
    return HttpResponseRedirect(reverse('gallery.gallery', args=[media_type]))


def media(request, media_id, media_type='image'):
    """The media page."""
    media, media_format = _get_media_info(media_id, media_type)
    return jingo.render(request, 'gallery/media.html',
                        {'media': media,
                         'media_format': media_format,
                         'media_type': media_type})


def _get_media_info(media_id, media_type):
    """Returns an image or video along with media format for the image."""
    media_format = None
    if media_type == 'image':
        media = get_object_or_404(Image, pk=media_id)
        media_format = imghdr.what(media.file.path)
    elif media_type == 'video':
        media = get_object_or_404(Video, pk=media_id)
    else:
        raise Http404
    return (media, media_format)


@login_required
@require_POST
@xframe_sameorigin
def upload_async(request, media_type='image'):
    """Upload images or videos from request.FILES."""

    try:
        if media_type == 'image':
            file_info = upload_image(request)
        else:
            file_info = upload_video(request)
    except FileTooLargeError as e:
        return HttpResponseBadRequest(
            json.dumps({'status': 'error', 'message': e.args[0]}))

    if isinstance(file_info, dict) and 'thumbnail_url' in file_info:
        return HttpResponse(
            json.dumps({'status': 'success', 'file': file_info}))

    message = MSG_FAIL_UPLOAD[media_type]
    return HttpResponseBadRequest(
        json.dumps({'status': 'error', 'message': message,
                    'errors': file_info}))

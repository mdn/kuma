import json
import logging

from functools import partial

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.datastructures import SortedDict
from django.views.decorators.http import require_GET

import jinja2
from tower import ugettext_lazy as _lazy, ugettext as _
from waffle.decorators import waffle_flag

from dashboards.readouts import (overview_rows, READOUTS, L10N_READOUTS,
                                 CONTRIBUTOR_READOUTS)
from sumo_locales import LOCALES
from sumo.parser import get_object_fallback
from sumo.urlresolvers import reverse
from sumo.utils import smart_int

from users.helpers import ban_link

from wiki.events import (ApproveRevisionInLocaleEvent,
                         ReviewableRevisionInLocaleEvent)
from wiki.models import Document, Revision
from wiki.views import SHOWFOR_DATA
from wiki.helpers import format_comment

from datetime import datetime


HOME_DOCS = {'quick': 'Home page - Quick', 'explore': 'Home page - Explore'}
MOBILE_DOCS = {'quick': 'Mobile home - Quick',
               'explore': 'Mobile home - Explore'}
PAGE_SIZE = 100


def home(request):
    data = {}
    for side, title in HOME_DOCS.iteritems():
        message = _lazy(u'The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return render(request, 'dashboards/home.html', data)


def mobile(request):
    data = {}
    for side, title in MOBILE_DOCS.iteritems():
        message = _lazy(u'The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return render(request, 'dashboards/mobile.html', data)


def _kb_readout(request, readout_slug, readouts, locale=None, mode=None):
    """Instantiate and return the readout with the given slug.

    Raise Http404 if there is no such readout.

    """
    if readout_slug not in readouts:
        raise Http404
    return readouts[readout_slug](request, locale=locale, mode=mode)


def _kb_detail(request, readout_slug, readouts, main_view_name,
               main_dash_title, locale=None):
    """Show all the rows for the given KB article statistics table."""
    return render(request, 'dashboards/kb_detail.html',
        {'readout': _kb_readout(request, readout_slug, readouts, locale),
         'locale': locale,
         'main_dash_view': main_view_name,
         'main_dash_title': main_dash_title})


@require_GET
def contributors_detail(request, readout_slug):
    """Show all the rows for the given contributor dashboard table."""
    return _kb_detail(request, readout_slug, CONTRIBUTOR_READOUTS,
                      'dashboards.contributors', _('Contributor Dashboard'),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)


@require_GET
def localization_detail(request, readout_slug):
    """Show all the rows for the given localizer dashboard table."""
    return _kb_detail(request, readout_slug, L10N_READOUTS,
                      'dashboards.localization', _('Localization Dashboard'))


def _kb_main(request, readouts, template, locale=None, extra_data=None):
    """Render a KB statistics overview page.

    Use the given template, pass the template the given readouts, limit the
    considered data to the given locale, and pass along anything in the
    `extra_data` dict to the template in addition to the standard data.

    """
    data = {'readouts': SortedDict((slug, class_(request, locale=locale))
                         for slug, class_ in readouts.iteritems()),
            'default_locale': settings.WIKI_DEFAULT_LANGUAGE,
            'default_locale_name':
                LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
            'current_locale_name': LOCALES[request.locale].native,
            'is_watching_approved': ApproveRevisionInLocaleEvent.is_notifying(
                request.user, locale=request.locale),
            'is_watching_locale': ReviewableRevisionInLocaleEvent.is_notifying(
                request.user, locale=request.locale),
            'is_watching_approved_default':
                ApproveRevisionInLocaleEvent.is_notifying(
                    request.user, locale=settings.WIKI_DEFAULT_LANGUAGE)}
    if extra_data:
        data.update(extra_data)
    return render(request, 'dashboards/' + template, data)


@require_GET
def localization(request):
    """Render aggregate data about articles in a non-default locale."""
    if request.locale == settings.WIKI_DEFAULT_LANGUAGE:
        return HttpResponseRedirect(reverse('dashboards.contributors'))
    data = {'overview_rows': partial(overview_rows, request.locale)}
    return _kb_main(request, L10N_READOUTS, 'localization.html',
                    extra_data=data)


@require_GET
def contributors(request):
    """Render aggregate data about the articles in the default locale."""
    return _kb_main(request, CONTRIBUTOR_READOUTS, 'contributors.html',
                    locale=settings.WIKI_DEFAULT_LANGUAGE)


@require_GET
def revisions(request):
    """Dashboard for reviewing revisions"""
    if request.is_ajax():
        username = request.GET.get('user', None)
        locale = request.GET.get('locale', None)
        topic = request.GET.get('topic', None)
        newusers = request.GET.get('newusers', None)

        display_start = int(request.GET.get('iDisplayStart', 0))

        revisions = (Revision.objects.select_related('creator').all()
                     .order_by('-created')
                     .defer('content'))

        # apply filters, limits, and pages
        if username:
            revisions = (revisions
                         .filter(creator__username__istartswith=username))
        if locale:
            revisions = revisions.filter(document__locale=locale)

        if topic:
            revisions = revisions.filter(slug__icontains=topic)

        if newusers:
            """Users with the first edit not older than 7 days or
               with fewer than 20 revisions at all"""
            sql = """SELECT id, creator_id, MIN(created)
                     FROM wiki_revision
                     GROUP BY creator_id
                     HAVING COUNT(*) <= 20
                     OR MIN(created) >= DATE_SUB(NOW(), INTERVAL 7 DAY)"""
            result = list(Revision.objects.raw(sql))
            if result:
                users = [u.creator_id for u in result]
                revisions = revisions.filter(creator__id__in=users)
            else:
                revisions = Revision.objects.none()

        total = revisions.count()
        revisions = revisions[display_start:display_start + PAGE_SIZE]

        # build the master JSON
        revision_json = {
            'iTotalRecords': total,
            'iTotalDisplayRecords': total,
            'aaData': []
        }
        for rev in revisions:
            prev = rev.get_previous()
            from_rev = str(prev.id if prev else rev.id)
            doc_url = reverse('wiki.document', args=[rev.document.full_path],
                              locale=rev.document.locale)
            articleUrl = '<a href="%s" target="_blank">%s</a>' % (doc_url,
                    jinja2.escape(rev.document.slug))
            articleLocale = ('<span class="dash-locale">%s</span>'
                             % rev.document.locale)
            articleComment = ('<span class="dashboard-comment">%s</span>'
                              % format_comment(rev))
            articleIsNew = ''
            if rev.based_on_id is None and not rev.document.is_redirect:
                articleIsNew = '<span class="dashboard-new">New: </span>'
            richTitle = (articleIsNew + articleUrl + articleLocale +
                         articleComment)

            revision_json['aaData'].append({
                'id': rev.id,
                'prev_id': from_rev,
                'doc_url': doc_url,
                'edit_url': reverse('wiki.edit_document',
                    args=[rev.document.full_path], locale=rev.document.locale),
                'compare_url': reverse('wiki.compare_revisions',
                    args=[rev.document.full_path], locale=rev.document.locale)
                    + '?from=%s&to=%s&raw=1' % (from_rev, str(rev.id)),
                'revert_url': reverse('wiki.revert_document',
                    args=[rev.document.full_path, rev.id],
                    locale=rev.document.locale),
                'history_url': reverse('wiki.document_revisions',
                    args=[rev.document.full_path], locale=rev.document.locale),
                'creator': ('<a href="" class="creator">%s</a>'
                            % jinja2.escape(rev.creator.username)),
                'title': rev.title,
                'richTitle': richTitle,
                'date': rev.created.strftime('%b %d, %y - %H:%M'),
                'slug': rev.document.slug,
                'ban_link': ban_link(rev.creator, request.user)
            })

        result = json.dumps(revision_json)
        return HttpResponse(result, mimetype='application/json')

    return render(request, 'dashboards/revisions.html')


@require_GET
def user_lookup(request):
    """Returns partial username matches"""
    userlist = []

    if request.is_ajax():
        user = request.GET.get('user', '')
        if user:
            matches = User.objects.filter(username__istartswith=user)
            for u in matches:
                userlist.append({'label': u.username})

    data = json.dumps(userlist)
    return HttpResponse(data,
                        content_type='application/json; charset=utf-8')


@require_GET
def topic_lookup(request):
    """Returns partial topic matches"""
    topiclist = []

    if request.is_ajax():
        topic = request.GET.get('topic', '')
        if topic:
            matches = Document.objects.filter(slug__icontains=topic)
            for d in matches:
                topiclist.append({'label': d.slug})

    data = json.dumps(topiclist)
    return HttpResponse(data,
                        content_type='application/json; charset=utf-8')


@require_GET
def wiki_rows(request, readout_slug):
    """Return the table contents HTML for the given readout and mode."""
    readout = _kb_readout(request, readout_slug, READOUTS,
                          locale=request.GET.get('locale'),
                          mode=smart_int(request.GET.get('mode'), None))
    max_rows = smart_int(request.GET.get('max'), fallback=None)
    return HttpResponse(readout.render(max_rows=max_rows))

import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.db.models import F

from jinja2 import escape
from waffle.decorators import waffle_flag

from sumo.urlresolvers import reverse

from users.helpers import ban_link

from wiki.models import Document, Revision
from wiki.helpers import format_comment

from . import (DEFAULT_LOCALE, LOCALES, ORDERS, LANGUAGES,
               LOCALIZATION_FLAGS, WAFFLE_FLAG, PAGE_SIZE)


@require_GET
@login_required
def fetch_localization_data(request):
    locale = request.GET.get('locale')
    topic = request.GET.get('topic', '')
    orderby = request.GET.get('orderby', '-modified')
    localization_flags = request.GET.get('localization_flags', 'update-needed')
    
    display_start = int(request.GET.get('iDisplayStart', 0))

    docs = (Document.objects.exclude(locale=DEFAULT_LOCALE)
            .exclude(is_redirect=True)
            .defer('html', 'rendered_html'))

    if orderby and orderby in dict(ORDERS):
        docs = docs.order_by(orderby)
    else:
        docs = docs.order_by('-modified')

    # Build up a dict of the filter conditions, if any, then apply
    # them all in one go.
    query_kwargs = {}
    
    if locale and locale in LANGUAGES:
        query_kwargs['locale'] = locale
        
    # Filter out documents where we can't compare to a parent (English) document
    query_kwargs['parent__isnull'] = False

    # We want to see outdated locale documents
    if localization_flags == 'update-needed':
        query_kwargs['modified__lt'] = F('parent__modified')
    # We want to see docs with missing parents explicitly
    elif localization_flags == 'missing-parent':
        query_kwargs['parent__isnull'] = True
    elif (localization_flags and localization_flags in LOCALIZATION_FLAGS):
        query_kwargs['current_revision__localization_tags__name'] = localization_flags

    if topic:
        query_kwargs['slug__icontains'] = topic
        
    if query_kwargs:
            docs = docs.filter(**query_kwargs)
            total = docs.count()
    else:
        # If no filters, just do a straight count(). It's the same
        # result, but much faster to compute.
        total = docs.count()
        
    if total >= display_start:
        # Only bother with this if we're actually going to get
        # some documents from it. Otherwise it's a pointless but
        # potentially complex query.
        docs = docs[display_start:display_start + PAGE_SIZE]

    json_response = {
        'iTotalRecords': total,
        'iTotalDisplayRecords': total,
        'aaData': []
    }
    for doc in docs:
        locale = '%s (%s)' % (doc.language, doc.locale)
        title = '<a href="%s">%s</a>' % (doc.get_absolute_url(), escape(doc.title))
        rev_date = (doc.current_revision.created.strftime('%b %d, %y - %H:%M')
                    if doc.current_revision else '')
        p = doc.parent
        if p:
            p_c = p.current_revision
            parent_title = '<a href="%s">%s</a>' % (p_c.get_absolute_url(), escape(p_c.title))
            parent_rev_date = p_c.created.strftime('%b %d, %y - %H:%M')
        else:
            parent_title = parent_rev_date = ''

        json_response['aaData'].append({
            'locale': locale,
            'title': title,
            'rev_date': rev_date,
            'parent_title': parent_title,
            'parent_rev_date': parent_rev_date,
        })

    result = json.dumps(json_response)
    return HttpResponse(result, mimetype='application/json')


@require_GET
@waffle_flag(WAFFLE_FLAG)
@login_required
def localization(request):
    locale = request.GET.get('locale')
    topic = request.GET.get('topic', None)
    orderby = request.GET.get('orderby')
    localization_flags = request.GET.get('localization_flags')

    filters = {
        'locale': locale,
        'localization_flags': localization_flags,
        'orderby': orderby,
    }
    filter_data = {
        'locales': LOCALES,
        'orderby_list': ORDERS,
        'flag_list': LOCALIZATION_FLAGS,
    }
    params = {
        'filters': filters,
        'filter_data': filter_data,
    }
    return render(request, 'dashboards/localization.html', params)


@require_GET
def revisions(request):
    """Dashboard for reviewing revisions"""
    if request.is_ajax():
        username = request.GET.get('user', None)
        locale = request.GET.get('locale', None)
        topic = request.GET.get('topic', None)
        newusers = request.GET.get('newusers', None)

        display_start = int(request.GET.get('iDisplayStart', 0))

        revisions = (Revision.objects.select_related('creator')
                     .order_by('-created')
                     .defer('content'))

        # Build up a dict of the filter conditions, if any, then apply
        # them all in one go.
        query_kwargs = {}
        if username:
            query_kwargs['creator__username__istartswith'] = username
        if locale:
            query_kwargs['document__locale'] = locale
        if topic:
            query_kwargs['slug__icontains'] = topic
        if newusers:
            # Users with the first edit not older than 7 days or
            # with fewer than 20 revisions at all
            sql = """SELECT id, creator_id, MIN(created)
                     FROM wiki_revision
                     GROUP BY creator_id
                     HAVING COUNT(*) <= 20
                     OR MIN(created) >= DATE_SUB(NOW(), INTERVAL 7 DAY)"""
            result = list(Revision.objects.raw(sql))
            if result:
                users = [u.creator_id for u in result]
                query_kwargs['creator__id__in'] = users
            else:
                revisions = Revision.objects.none()

        if query_kwargs:
            revisions = revisions.filter(**query_kwargs)
            total = revisions.count()
        else:
            # If no filters, just do a straight count(). It's the same
            # result, but much faster to compute.
            total = Revision.objects.count()

        if total >= display_start:
            # Only bother with this if we're actually going to get
            # some revisions from it. Otherwise it's a pointless but
            # potentially complex query.
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
                    escape(rev.document.slug))
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
                            % escape(rev.creator.username)),
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

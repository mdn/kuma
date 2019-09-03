from __future__ import division, unicode_literals

import datetime
import json

import waffle
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.decorators.vary import vary_on_headers

from kuma.core.decorators import (ensure_wiki_domain, login_required,
                                  shared_cache_control)
from kuma.core.utils import paginate
from kuma.wiki.kumascript import macro_usage
from kuma.wiki.models import Document, Revision

from . import PAGE_SIZE
from .forms import RevisionDashboardForm
from .jobs import SpamDashboardHistoricalStats


@ensure_wiki_domain
@shared_cache_control
def index(request):
    """Index of dashboards."""
    return render(request, 'dashboards/index.html')


@ensure_wiki_domain
@never_cache
@require_GET
@login_required
def revisions(request):
    """Dashboard for reviewing revisions"""

    filter_form = RevisionDashboardForm(request.GET)
    page = request.GET.get('page', 1)

    revisions = Revision.objects.order_by('-id').defer('content')

    query_kwargs = False
    exclude_kwargs = False

    # We can validate right away because no field is required
    if filter_form.is_valid():
        query_kwargs = {}
        exclude_kwargs = {}
        query_kwargs_map = {
            'user': 'creator__username__istartswith',
            'locale': 'document__locale',
            'topic': 'slug__icontains',
        }

        # Build up a dict of the filter conditions, if any, then apply
        # them all in one go.
        for fieldname, kwarg in query_kwargs_map.items():
            filter_arg = filter_form.cleaned_data[fieldname]
            if filter_arg:
                query_kwargs[kwarg] = filter_arg

        start_date = filter_form.cleaned_data['start_date']
        if start_date:
            end_date = (filter_form.cleaned_data['end_date'] or
                        datetime.datetime.now())
            query_kwargs['created__range'] = [start_date, end_date]

        preceding_period = filter_form.cleaned_data['preceding_period']
        if preceding_period:
            # these are messy but work with timedelta's seconds format,
            # and keep the form and url arguments human readable
            if preceding_period == 'month':
                seconds = 30 * 24 * 60 * 60
            if preceding_period == 'week':
                seconds = 7 * 24 * 60 * 60
            if preceding_period == 'day':
                seconds = 24 * 60 * 60
            if preceding_period == 'hour':
                seconds = 60 * 60
            # use the form date if present, otherwise, offset from now
            end_date = (filter_form.cleaned_data['end_date'] or
                        timezone.now())
            start_date = end_date - datetime.timedelta(seconds=seconds)
            query_kwargs['created__range'] = [start_date, end_date]

        authors_filter = filter_form.cleaned_data['authors']
        if ((not filter_form.cleaned_data['user']) and
           authors_filter not in ['', str(RevisionDashboardForm.ALL_AUTHORS)]):

            # Get the 'Known Authors' group.
            try:
                group = Group.objects.get(name="Known Authors")
            except Group.DoesNotExist:
                pass
            else:
                # If the filter is 'Known Authors', then query for the
                # 'Known Authors' group, otherwise the filter is
                # 'Unknown Authors', so exclude the 'Known Authors' group.
                if authors_filter == str(RevisionDashboardForm.KNOWN_AUTHORS):
                    query_kwargs['creator__groups__pk'] = group.pk
                else:
                    exclude_kwargs['creator__groups__pk'] = group.pk

    if query_kwargs or exclude_kwargs:
        revisions = revisions.filter(**query_kwargs).exclude(**exclude_kwargs)

    # prefetch_related needs to come after all filters have been applied to qs
    revisions = revisions.prefetch_related('creator__bans').prefetch_related(
        Prefetch('document', queryset=Document.admin_objects.only(
                 'deleted', 'locale', 'slug')))

    show_spam_submission = (
        request.user.is_authenticated and
        request.user.has_perm('wiki.add_revisionakismetsubmission'))
    if show_spam_submission:
        revisions = revisions.prefetch_related('akismet_submissions')

    revisions = paginate(request, revisions, per_page=PAGE_SIZE)

    context = {
        'revisions': revisions,
        'page': page,
        'show_ips': (
            waffle.switch_is_active('store_revision_ips') and
            request.user.is_superuser
        ),
        'show_spam_submission': show_spam_submission,
    }

    # Serve the response HTML conditionally upon request type
    if request.is_ajax():
        template = 'dashboards/includes/revision_dashboard_body.html'
    else:
        template = 'dashboards/revisions.html'
        context['form'] = filter_form

    return render(request, template, context)


@shared_cache_control
@vary_on_headers('X-Requested-With')
@require_GET
@login_required
def user_lookup(request):
    """Returns partial username matches"""
    userlist = []

    if request.is_ajax():
        user = request.GET.get('user', '')
        if user:
            matches = (get_user_model().objects
                       .filter(username__istartswith=user)
                       .order_by('username'))
            for username in matches.values_list('username', flat=True)[:20]:
                userlist.append({'label': username})

    data = json.dumps(userlist)
    return HttpResponse(data, content_type='application/json; charset=utf-8')


@shared_cache_control
@vary_on_headers('X-Requested-With')
@require_GET
@login_required
def topic_lookup(request):
    """Returns partial topic matches"""
    topiclist = []

    if request.is_ajax():
        topic = request.GET.get('topic', '')
        if topic:
            matches = (Document.objects.filter(slug__icontains=topic)
                       .order_by('slug'))
            for slug in matches.values_list('slug', flat=True)[:20]:
                topiclist.append({'label': slug})

    data = json.dumps(topiclist)
    return HttpResponse(data,
                        content_type='application/json; charset=utf-8')


@ensure_wiki_domain
@never_cache
@require_GET
@login_required
@permission_required((
    'wiki.add_revisionakismetsubmission',
    'wiki.add_documentspamattempt',
    'users.add_userban'), raise_exception=True)
def spam(request):
    """Dashboard for spam moderators."""

    # Combine data sources
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    data = SpamDashboardHistoricalStats().get(yesterday)

    if not data:
        return render(request, 'dashboards/spam.html', {'processing': True})

    return render(request, 'dashboards/spam.html', data)


@ensure_wiki_domain
@shared_cache_control
@require_GET
def macros(request):
    """Returns table of active macros and their page counts."""
    macros = macro_usage()
    total = sum(val['count'] for val in macros.values())
    context = {
        'macros': macros,
        'has_counts': total != 0
    }
    return render(request, 'dashboards/macros.html', context)

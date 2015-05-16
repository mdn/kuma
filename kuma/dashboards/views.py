import datetime
import json

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from kuma.wiki.models import Document, Revision
from kuma.core.utils import paginate

from .forms import RevisionDashboardForm
from . import PAGE_SIZE


@require_GET
def revisions(request):
    """Dashboard for reviewing revisions"""

    filter_form = RevisionDashboardForm(request.GET)
    page = request.GET.get('page', 1)

    revisions = (Revision.objects.select_related('creator')
                                 .order_by('-created')
                                 .defer('content'))

    query_kwargs = False

    # We can validate right away because no field is required
    if filter_form.is_valid():
        query_kwargs = {}
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
                        timezone.now())
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
            
    if query_kwargs:
        revisions = revisions.filter(**query_kwargs)
        total = revisions.count()
    else:
        # If no filters, just do a straight count(). It's the same
        # result, but much faster to compute.
        total = Revision.objects.count()

    # Only bother with this if we're actually going to get
    # some revisions from it. Otherwise it's a pointless but
    # potentially complex query.
    revisions = paginate(request, revisions, per_page=PAGE_SIZE)

    context = {'revisions': revisions, 'page': page, 'total': total}

    # Serve the response HTML conditionally upon reques type
    if request.is_ajax():
        template = 'dashboards/includes/revision_dashboard_body.html'
    else:
        template = 'dashboards/revisions.html'
        context['form'] = filter_form

    return render(request, template, context)


@require_GET
def user_lookup(request):
    """Returns partial username matches"""
    userlist = []

    if request.is_ajax():
        user = request.GET.get('user', '')
        if user:
            matches = User.objects.filter(username__istartswith=user)
            for match in matches:
                userlist.append({'label': match.username})

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
            for match in matches:
                topiclist.append({'label': match.slug})

    data = json.dumps(topiclist)
    return HttpResponse(data,
                        content_type='application/json; charset=utf-8')

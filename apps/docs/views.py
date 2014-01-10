import json
import os.path
import random

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render

import commonware
from dateutil.parser import parse as date_parse
from tower import ugettext as _

from feeder.models import Entry

from wiki.models import Document, REVIEW_FLAG_TAGS

log = commonware.log.getLogger('kuma.docs')

MAX_REVIEW_DOCS = 5


def docs(request):
    """Docs landing page."""

    # Accept ?next parameter for redirects from language selector.
    if 'next' in request.GET:
        next = request.GET['next']
        # Only accept site-relative paths, not absolute URLs to anywhere.
        if next.startswith('/'):
            return HttpResponseRedirect(next)

    # Recent updates
    active_docs = []
    entries = Entry.objects.filter(feed__shortname='mdc-latest')
    for entry in entries:
        parsed = entry.parsed
        if not parsed.title.lower().startswith('en/'):
            continue
        # L10n: "multiple" refers to more than one author.
        authorname = (parsed.author if not parsed.author == '(multiple)' else
                      _('(multiple)'))
        active_docs.append({
            'title': parsed.title[3:].replace('_', ' '),
            'link': parsed.link,
            'author': authorname
        })
        if len(active_docs) == 5:
            break

    review_flag_docs = dict()
    for tag, description in REVIEW_FLAG_TAGS:
        review_flag_docs[tag] = (Document.objects
            .filter_for_review(tag_name=tag)
            .order_by('-current_revision__created')
            .all()[:MAX_REVIEW_DOCS])

    data = {'active_docs': active_docs, 
            'review_flag_docs': review_flag_docs,
            'dotd': dotd}
    return render(request, 'docs/docs.html', data)

import json
import os.path
import random

from django.conf import settings

from caching.base import cached
import commonware
from dateutil.parser import parse as date_parse
import jingo
from tower import ugettext as _

from feeder.models import Entry

from wiki.models import Document, REVIEW_FLAG_TAGS

log = commonware.log.getLogger('kuma.docs')

MAX_REVIEW_DOCS = 5


def docs(request):
    """Docs landing page."""

    # Doc of the day
    dotd = cached(_get_popular_item, 'kuma_docs_dotd', 24*60*60)

    # Recent updates
    entries = Entry.objects.filter(feed__shortname='mdc-latest')
    active_docs = []
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
    return jingo.render(request, 'docs/docs.html', data)


def _get_popular_item():
    """Get a single, random item off the popular pages list."""
    try:
        pages = json.load(open(os.path.join(
            settings.MDC_PAGES_DIR, 'popular.json')))
    except Exception, e:
        log.error(e)
        return None

    try:
        page = random.choice(pages)
    except IndexError:
        return None

    # Maybe not the right place, but let's parse the timestamp.
    page['last_edit'] = date_parse(page['last_edit'])

    return page

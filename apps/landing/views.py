from django.conf import settings
from django.shortcuts import render
from django.views import static
from django.db import connection

import constance.config

from devmo import SECTION_USAGE
from kuma.demos.models import Submission
from kuma.feeder.models import Bundle


def home(request):
    """Home page."""
    demos = (Submission.objects.all_sorted('upandcoming').exclude(hidden=True))[:12]

    updates = []
    for s in SECTION_USAGE:
        updates += Bundle.objects.recent_entries(s.updates)[:5]

    community_stats = {}

    cursor = connection.cursor()

    cursor.execute("SELECT count(creator_id) \
                    FROM \
                      (SELECT DISTINCT creator_id \
                       FROM wiki_revision \
                       WHERE created >= DATE_SUB(NOW(), INTERVAL 1 YEAR)) AS contributors_last_12_month")
    contributors = cursor.fetchone()

    cursor.execute("SELECT count(locale) \
                    FROM \
                      (SELECT DISTINCT wd.locale \
                       FROM wiki_document wd, wiki_revision wr \
                       WHERE wd.id = wr.document_id \
                       AND wr.created >= DATE_SUB(NOW(), INTERVAL 1 YEAR)) AS locales_last_12_months")
    locales = cursor.fetchone()

    try:
        community_stats['contributors'] = contributors[0]
    except IndexError:
        community_stats['contributors'] = 5453

    try:
        community_stats['locales'] = locales[0]
    except IndexError:
        community_stats['locales'] = 36

    return render(request, 'landing/homepage.html',
            {'demos': demos, 'updates': updates, 'stats': community_stats,
                    'current_challenge_tag_name':
                    str(constance.config.DEMOS_DEVDERBY_CURRENT_CHALLENGE_TAG).strip()})


def contribute_json(request):
    return static.serve(request, 'contribute.json',
                        document_root=settings.ROOT)


def learn(request):
    """Learn landing page."""
    return render(request, 'landing/learn.html')


def learn_html(request):
    """HTML landing page."""
    return render(request, 'landing/learn_html.html')


def learn_css(request):
    """CSS landing page."""
    return render(request, 'landing/learn_css.html')


def learn_javascript(request):
    """JavaScript landing page."""
    return render(request, 'landing/learn_javascript.html')


def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return render(request, 'landing/promote_buttons.html')


def common_landing(request, section=None, extra=None):
    """Common code for landing pages."""
    if not section:
        raise NotImplementedError

    updates = Bundle.objects.recent_entries(section.updates)[:5]
    tweets = Bundle.objects.recent_entries(section.twitter)[:8]

    data = {'updates': updates, 'tweets': tweets}
    if extra:
        data.update(extra)

    return render(request, 'landing/%s.html' % section.short, data)

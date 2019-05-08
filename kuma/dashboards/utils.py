from __future__ import division, unicode_literals

import datetime
from collections import Counter, defaultdict

from dateutil import parser
from django.core.exceptions import ImproperlyConfigured
from six.moves import xrange

from kuma.wiki.models import (DocumentDeletionLog, DocumentSpamAttempt,
                              Revision, RevisionAkismetSubmission)
from kuma.wiki.utils import analytics_upageviews


# Rounded to nearby 7-day period for weekly cycles
SPAM_PERIODS = (
    (1, 'period_daily', 'Daily'),
    (7, 'period_weekly', 'Weekly'),
    (28, 'period_monthly', 'Monthly'),
    (91, 'period_quarterly', 'Quarterly'),
)


def date_range(start, end):
    """ Return an iterator providing the dates between `start` and `end`, inclusive.
    """
    if getattr(start, 'date', None) is not None:
        start = start.date()
    if getattr(end, 'date', None) is not None:
        end = end.date()
    days = (end - start).days + 1
    return (start + datetime.timedelta(days=d) for d in xrange(days))


def chunker(seq, size):
    for i in xrange(0, len(seq), size):
        yield seq[i:i + size]


def spam_day_stats(day):
    counts = Counter()
    next_day = day + datetime.timedelta(days=1)

    revs = Revision.objects.filter(
        created__range=(day, next_day)
    ).only('id').prefetch_related('akismet_submissions')
    for rev in revs:
        if any(a.type == 'spam' for a in rev.akismet_submissions.all()):
            counts['published_spam'] += 1
        else:
            counts['published_ham'] += 1

    needs_review = False
    blocked_edits = DocumentSpamAttempt.objects.filter(
        created__range=(day, next_day)).only('review')
    for blocked in blocked_edits:
        # Is it a false positive?
        if blocked.review == DocumentSpamAttempt.HAM:
            counts['blocked_ham'] += 1
        elif blocked.review == DocumentSpamAttempt.SPAM:
            counts['blocked_spam'] += 1
        else:
            if blocked.review == DocumentSpamAttempt.NEEDS_REVIEW:
                needs_review = True
            continue

    events = {
        'published_spam': 0,
        'published_ham': 0,
        'blocked_spam': 0,
        'blocked_ham': 0,
    }
    events.update(counts)

    return {
        'version': 1,
        'generated': datetime.datetime.now().isoformat(),
        'day': day.isoformat(),
        'needs_review': needs_review,
        'events': events
    }


def spam_dashboard_historical_stats(periods=None, end_date=None):
    """
    Gather spam statistics for a range of dates.

    Keywords Arguments:
    periods - a sequence of (days, identifier, name) tuples
    end_date - The ending anchor date for the statistics
    """
    from .jobs import SpamDayStats, SpamDashboardRecentEvents

    periods = periods or SPAM_PERIODS
    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    end_date = end_date or (datetime.date.today() - datetime.timedelta(days=1))

    longest = max(days for days, identifier, name in periods)
    spans = [
        (identifier,
         days,
         name,
         end_date - datetime.timedelta(days=days - 1),  # current period begins
         end_date)
        for days, identifier, name in periods
    ]

    start_date = end_date - datetime.timedelta(days=longest - 1)
    dates = date_range(start_date, end_date)

    # Iterate over the daily stats
    job = SpamDayStats()
    trends = defaultdict(Counter)
    for day in dates:
        # Gather daily raw stats
        raw_events = job.get(day)
        day_events = raw_events['events']

        # Regenerate stats if there are change attempts with
        # needs_review marked and the data is stale.
        if raw_events['needs_review']:
            generated = parser.parse(raw_events['generated'])

            age = datetime.datetime.now() - generated
            if age.total_seconds() > 300:
                job.invalidate(day)

        # Accumulate trends over periods
        for period_id, length, period_name, start, end in spans:
            # Sum up the items in day_events with any items that may
            # already be in the Counter at trends[period_id]
            if start <= day <= end:
                trends[period_id].update(day_events)

    # Prepare output data
    data = {
        'version': 1,
        'generated': datetime.datetime.now().isoformat(),
        'end_date': end_date,
        'periods': periods,
        'trends': [],
    }

    job = SpamDashboardRecentEvents()
    events_data = job.get(start_date, end_date + datetime.timedelta(days=1)) or {}

    # Calculate positive and negative rates
    for period_id, length, period_name, start, end in spans:
        period = trends[period_id]
        previous_start = start - datetime.timedelta(days=length)
        previous_end = start - datetime.timedelta(days=1)

        # Accumulate the spam viewer counts for the previous and
        # current periods of this length.
        period['spam_viewers'] = 0
        period['spam_viewers_previous'] = 0
        for item in events_data.get('recent_spam', ()):
            if start <= item['date'] <= end:
                period['spam_viewers'] += item.get('viewers', 0)
            elif previous_start <= item['date'] <= previous_end:
                period['spam_viewers_previous'] += item.get('viewers', 0)

        period['spam_viewers_daily_average'] = period['spam_viewers'] / length
        if period['spam_viewers_previous']:
            delta = period['spam_viewers'] - period['spam_viewers_previous']
            period['spam_viewers_change'] = delta / period['spam_viewers_previous']

        spam = period['published_spam'] + period['blocked_spam']
        ham = period['published_ham'] + period['blocked_ham']

        if spam:
            period['true_positive_rate'] = period['blocked_spam'] / spam
        else:
            period['true_positive_rate'] = 1.0

        if ham:
            period['true_negative_rate'] = period['published_ham'] / ham
        else:
            period['true_negative_rate'] = 1.0

        data['trends'].append({
            'id': period_id,
            'name': period_name,
            'days': length,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'stats': period,
        })

    data.update(events_data)
    return data


def spam_dashboard_recent_events(start=None, end=None):
    """Gather data for recent spam events."""
    now = datetime.datetime.now()
    data = {
        'events_generated': str(now),
        'recent_spam': [],
    }

    # Define the start and end dates/datetimes.
    if not end:
        end = now
    if not start:
        start = end - datetime.timedelta(days=183)

    # Gather recent published spam
    recent_spam = RevisionAkismetSubmission.objects.filter(
        type='spam',
        revision__created__gt=start,
        revision__created__lt=end
    ).select_related(
        'revision__document'
    ).order_by('-id')

    # Document is new; document is a translation
    change_types = {
        (False, False): "New Page",
        (True, False): "Page Edit",
        (False, True): "New Translation",
        (True, True): "Translation Update",
    }

    for rs in recent_spam:
        revision = rs.revision
        document = revision.document

        # We only care about the spam rev and the one immediately
        # following, if there is one.
        revisions = list(
            document.revisions.filter(
                id__gte=revision.id
            ).only('id', 'created').order_by('id')[:2]
        )

        # How long was it active?
        if len(revisions) == 1:
            time_active = 'Current'
        else:
            next_rev = revisions[1]
            time_active_raw = next_rev.created - revision.created
            time_active = int(time_active_raw.total_seconds())

        change_type = change_types[bool(revision.previous), bool(document.parent)]

        # Gather table data
        data['recent_spam'].append({
            'date': revision.created.date(),
            'time_active': time_active,
            'revision_id': revision.id,
            'revision_path': revision.get_absolute_url(),
            'change_type': change_type,
            'document_path': revision.document.get_absolute_url(),
        })

    # Update the data with the number of viewers from Google Analytics.
    for chunk in chunker(data['recent_spam'], 250):
        start_date = min(item['date'] for item in chunk)
        revs = [item['revision_id'] for item in chunk]

        try:
            views = analytics_upageviews(revs, start_date)
        except ImproperlyConfigured as e:
            data['improperly_configured'] = str(e)
            break

        for item in chunk:
            item['viewers'] = views[item['revision_id']]

    return data

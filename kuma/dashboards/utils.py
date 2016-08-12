from __future__ import division
from collections import defaultdict, Counter
import datetime

from dateutil import parser
from django.utils import timezone

from kuma.wiki.models import (DocumentDeletionLog, RevisionAkismetSubmission,
                              Revision, DocumentSpamAttempt)


# Rounded to nearby 7-day period for weekly cycles
SPAM_PERIODS = (
    (1, 'period_daily'),
    (7, 'period_weekly'),
    (28, 'period_monthly'),
    (91, 'period_quarterly'),
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
    periods - a sequence of (days, name) tuples
    end_date - The ending anchor date for the statistics
    """
    from .jobs import SpamDayStats

    periods = periods or SPAM_PERIODS
    end_date = end_date or (datetime.date.today() - datetime.timedelta(days=1))

    longest = max(days for days, identifier in periods)
    spans = [
        (identifier,
         days,
         end_date - datetime.timedelta(days=days - 1),  # current period begins
         end_date)
        for days, identifier in periods
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
        for period_id, length, start, end in spans:
            # Sum up the items in day_events with any items that may
            # already be in the Counter at trends[period_id]
            if start <= day <= end:
                trends[period_id].update(day_events)

    # Calculate positive and negative rates
    for period_id, length, start, end in spans:
        current = trends[period_id]
        spam = current['published_spam'] + current['blocked_spam']
        ham = current['published_ham'] + current['blocked_ham']

        if spam:
            current['true_positive_rate'] = current['blocked_spam'] / spam
        else:
            current['true_positive_rate'] = 1.0

        if ham:
            current['true_negative_rate'] = current['published_ham'] / ham
        else:
            current['true_negative_rate'] = 1.0

    # Prepare output data
    data = {
        'version': 1,
        'generated': datetime.datetime.now().isoformat(),
        'trends': trends,
    }

    return data


def spam_dashboard_recent_events(start_date=None):
    """Gather data for recent spam events."""
    now = timezone.now()
    data = {
        'now': now,
        'recent_spam': [],
    }
    if not start_date:
        start_date = now - datetime.timedelta(days=181)

    # Gather recent published spam
    recent_spam = RevisionAkismetSubmission.objects.filter(
        type='spam', revision__created__gt=start_date
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
            if document.deleted:
                try:
                    entry = DocumentDeletionLog.objects.filter(
                        locale=document.locale, slug=document.slug
                    ).latest('id')
                    time_active_raw = entry.timestamp - revision.created
                    time_active = int(time_active_raw.total_seconds())
                except DocumentDeletionLog.DoesNotExist:
                    time_active = 'Deleted'
            else:
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

    return data

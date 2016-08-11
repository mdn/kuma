from collections import defaultdict
import datetime

from django.utils import timezone

from kuma.wiki.models import (DocumentDeletionLog, RevisionAkismetSubmission,
                              Revision, DocumentSpamAttempt)


def spam_day_stats(day):
    counts = defaultdict(int)
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

    return {
        'version': 1,
        'generated': datetime.datetime.now().isoformat(),
        'day': day.isoformat(),
        'needs_review': needs_review,
        'events': dict(counts)
    }


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

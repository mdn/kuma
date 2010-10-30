import datetime
import time

from django.core import paginator
from django.utils.http import urlencode
from django.utils.tzinfo import LocalTimezone

from tower import ungettext


def paginate(request, queryset, per_page=20):
    """Get a Paginator, abstracting some common paging actions."""
    p = paginator.Paginator(queryset, per_page)

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # Get a page of results, or the first page if there's a problem.
    try:
        paginated = p.page(page)
    except (paginator.EmptyPage, paginator.InvalidPage):
        paginated = p.page(1)

    base = request.build_absolute_uri(request.path)

    items = [(k, v) for k in request.GET if k != 'page'
             for v in request.GET.getlist(k) if v]

    qsa = urlencode(items)

    paginated.url = u'%s?%s' % (base, qsa)
    return paginated


def timesince(d, now=None):
    """Take two datetime objects and return the time between d and now as a
    nicely formatted string, e.g. "10 minutes".  If d occurs after now, return
    "".

    Units used are years, months, weeks, days, hours, and minutes. Seconds and
    microseconds are ignored.  Just one unit is displayed.  For example,
    "2 weeks" and "1 year" are possible outputs, but "2 weeks, 3 days" and "1
    year, 5 months" are not.

    Adapted from django.utils.timesince to have better i18n (not assuming
    commas as list separators and including "ago" so order of words isn't
    assumed), show only one time unit, and include seconds.

    """
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('%(number)d year ago',
                                               '%(number)d years ago', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('%(number)d month ago',
                                              '%(number)d months ago', n)),
      (60 * 60 * 24 * 7, lambda n: ungettext('%(number)d week ago',
                                             '%(number)d weeks ago', n)),
      (60 * 60 * 24, lambda n: ungettext('%(number)d day ago',
                                         '%(number)d days ago', n)),
      (60 * 60, lambda n: ungettext('%(number)d hour ago',
                                    '%(number)d hours ago', n)),
      (60, lambda n: ungettext('%(number)d minute ago',
                               '%(number)d minutes ago', n)),
      (1, lambda n: ungettext('%(number)d second ago',
                               '%(number)d seconds ago', n))
    )
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        if d.tzinfo:
            now = datetime.datetime.now(LocalTimezone(d))
        else:
            now = datetime.datetime.now()

    # Ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u''
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    return name(count) % {'number': count}

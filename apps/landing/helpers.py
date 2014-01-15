import datetime

from django.conf import settings

from jingo import register
import jinja2
import pytz
import re

from decimal import Decimal
from django.utils.formats import number_format


from devmo import SECTIONS, SECTION_USAGE


@register.inclusion_tag('landing/newsfeed.html')
def newsfeed(entries, section_headers=False):
    """Landing page news feed."""
    return {'updates': entries, 'section_headers': section_headers}


@register.inclusion_tag('landing/discussions.html')
def discussions_feed(entries):
    """Landing page news feed."""
    return {'updates': entries}


@register.inclusion_tag('sidebar/twitter.html')
@jinja2.contextfunction
def twitter(context, tweets, title=None):
    """Twitter box in the sidebar."""
    tweet_data = []
    for tweet in tweets:
        (nick, status) = tweet.parsed.summary.split(':', 1)
        published = datetime.datetime(*tweet.parsed.updated_parsed[:6],
                                      tzinfo=pytz.utc)

        tweet_data.append({
            'nick': nick,
            'status': status,
            'section': tweet.section,
            'link': tweet.parsed.link,
            'published': published,
        })

    c = dict(context.items())
    c.update({'tweets': tweet_data, 'tweet_qs': tweets,
              'title': title})
    return c


@register.filter()
def intcomma(value, use_l10n=True):
    """
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    """
    if settings.USE_L10N and use_l10n:
        try:
            if not isinstance(value, (float, Decimal)):
                value = int(value)
        except (TypeError, ValueError):
            return intcomma(value, False)
        else:
            return number_format(value, force_grouping=True)
    orig = force_text(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', orig)
    if orig == new:
        return new
    else:
        return intcomma(new, use_l10n)
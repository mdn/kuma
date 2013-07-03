# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime

from django.conf import settings

from jingo import register
import jinja2
import pytz

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

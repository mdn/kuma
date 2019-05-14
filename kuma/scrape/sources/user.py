"""UserSource scrapes MDN user profiles."""
from __future__ import absolute_import, unicode_literals

import dateutil

from kuma.core.utils import safer_pyquery as pq

from .base import Source


class UserSource(Source):
    """Scrape a user's profile."""

    PARAM_NAME = 'username'

    OPTIONS = {
        'force': ('bool', False),   # Update existing User records
        'social': ('bool', False),  # Scrape social links
        'email': ('text', ''),      # Set the email for the User
    }

    def load_and_validate_existing(self, storage):
        """Load user data from previous runs."""
        user = None
        if not self.force:
            user = storage.get_user(self.username)
        return user is not None, []

    def source_path(self):
        """MDN path for this user."""
        return '/en-US/profiles/%s' % self.username

    def load_prereqs(self, requester, storage):
        """Load and process the profile HTML."""
        response = requester.request(self.source_path(),
                                     raise_for_status=False)
        if response.status_code == 200:
            data = self.extract_data(response.content)
        elif (response.status_code == 404 and
                self.is_banned(response.content)):
            data = {
                'username': self.username,
                'banned': True
            }
        else:
            raise self.SourceError('status code %s', response.status_code)
        if self.email:
            data['email'] = self.email
        return True, data

    def save_data(self, storage, data):
        """Save the user data for future calls."""
        storage.save_user(data)
        return []

    def extract_data(self, html):
        """Extract user data from profile HTML."""
        data = {}
        parsed = pq(html)
        username_elem = parsed.find("h1.user-title span.nickname")[0]
        data['username'] = username_elem.text
        fullname_elems = parsed.find("h1.user-title span.fn")
        if fullname_elems:
            data['fullname'] = fullname_elems[0].text

        if parsed.find('ul.user-info'):
            for cls, name in (
                    ('title', 'title'),
                    ('org', 'organization'),
                    ('loc', 'location'),
                    ('irc', 'irc_nickname')):
                elem = parsed.find('ul.user-info li.%s' % cls)
                if elem:
                    if cls == 'irc':
                        raw = elem[0].text
                        data[name] = raw.replace('IRC: ', '')
                    else:
                        data[name] = elem[0].text

        tags_divs = parsed.find("div.user-tags")
        for tag_div in tags_divs:
            h2 = tag_div.find('h2')
            if 'Interests' in h2.text:
                tag_type = 'interest'
            else:
                assert 'Expertise' in h2.text
                tag_type = 'expertise'
            tags = sorted([tag.text for tag in tag_div.cssselect('span')])
            data[tag_type] = tags

        if self.social:
            socials = ('twitter', 'github', 'stackoverflow', 'linkedin',
                       'mozillians', 'facebook')
            for social in socials:
                cssselect = 'ul.user-links li.%s a' % social
                social_elem = parsed.find(cssselect)
                if social_elem:
                    social_href = self.decode_href(social_elem.attr('href'))
                    data['%s_url' % social] = social_href

        since_elem = parsed.find('div.user-since time')
        raw_date_joined = since_elem.attr('datetime')
        date_joined = dateutil.parser.parse(raw_date_joined)
        data['date_joined'] = date_joined.replace(tzinfo=None)

        return data

    def is_banned(self, html):
        """Detect if a 404 is for a banned user."""
        parsed = pq(html)
        ban_text = parsed.find('p.notice')
        return 'banned' in ban_text.text()

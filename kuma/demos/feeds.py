import datetime
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import (Atom1Feed, SyndicationFeed,
                                        Rss201rev2Feed)
from django.utils.translation import ugettext as _

import jingo

from kuma.core.validators import valid_jsonp_callback_value
from kuma.core.urlresolvers import reverse
from kuma.users.helpers import gravatar_url

from . import TAG_DESCRIPTIONS
from .models import Submission


MAX_FEED_ITEMS = getattr(settings, 'MAX_FEED_ITEMS', 15)


class SubmissionJSONFeedGenerator(SyndicationFeed):
    """JSON feed generator for Submissions
    TODO: Someday maybe make this into a JSON Activity Stream?"""
    mime_type = 'application/json'

    def _encode_complex(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

    def write(self, outfile, encoding):
        request = self.feed['request']

        # Check for a callback param, validate it before use
        callback = request.GET.get('callback', None)
        if callback is not None:
            if not valid_jsonp_callback_value(callback):
                callback = None

        items_out = []
        for item in self.items:

            # Include some of the simple elements from the preprocessed feed item
            item_out = dict((x, item[x]) for x in (
                'link', 'title', 'pubdate', 'author_name', 'author_link',
            ))

            if item['obj'].creator.email:
                item_out['author_avatar'] = gravatar_url(item['obj'].creator)

            # Linkify the tags used in the feed item
            item_out['categories'] = dict(
                (x, request.build_absolute_uri(reverse('demos_tag', kwargs={'tag': x})))
                for x in item['categories']
            )

            # Include a few more, raw from the submission object itself.
            item_out.update((x, unicode(getattr(item['obj'], x))) for x in (
                'summary', 'description',
            ))

            item_out['featured'] = item['obj'].featured

            # Include screenshot as an absolute URL.
            item_out['screenshot'] = request.build_absolute_uri(
                item['obj'].screenshot_url(1))

            # HACK: This .replace() should probably be done in the model
            item_out['thumbnail'] = request.build_absolute_uri(
                item['obj'].thumbnail_url(1))

            # TODO: What else might be useful in a JSON feed of demo submissions?
            # Comment, like, view counts may change too much for caching to be useful

            items_out.append(item_out)

        data = items_out

        if callback:
            outfile.write('%s(' % callback)
        outfile.write(json.dumps(data, default=self._encode_complex))
        if callback:
            outfile.write(')')


class SubmissionsFeed(Feed):
    title = _('MDN demos')
    subtitle = _('Demos submitted by MDN users')
    link = '/'

    def __call__(self, request, *args, **kwargs):
        self.request = request
        return super(SubmissionsFeed, self).__call__(request, *args, **kwargs)

    def feed_extra_kwargs(self, obj):
        return {'request': self.request}

    def item_extra_kwargs(self, obj):
        return {'obj': obj}

    def get_object(self, request, format):
        if format == 'json':
            self.feed_type = SubmissionJSONFeedGenerator
        elif format == 'rss':
            self.feed_type = Rss201rev2Feed
        else:
            self.feed_type = Atom1Feed

    def item_pubdate(self, submission):
        return submission.modified

    def item_title(self, submission):
        return submission.title

    def item_description(self, submission):
        return jingo.render_to_string(
            self.request,
            'demos/feed_item_description.html', dict(
                request=self.request, submission=submission
            )
        )

    def item_author_name(self, submission):
        return '%s' % submission.creator

    def item_author_link(self, submission):
        return self.request.build_absolute_uri(
            reverse('kuma.demos.views.profile_detail',
                    args=(submission.creator.username,)))

    def item_link(self, submission):
        return self.request.build_absolute_uri(
            reverse('kuma.demos.views.detail',
                    args=(submission.slug,)))

    def item_categories(self, submission):
        return submission.taggit_tags.all()

    def item_copyright(self, submission):
        # TODO: Translate license name to something meaningful in the feed
        return submission.license_name

    def item_enclosure_url(self, submission):
        return self.request.build_absolute_uri(submission.demo_package.url)

    def item_enclosure_length(self, submission):
        return submission.demo_package.size

    def item_enclosure_mime_type(self, submission):
        return 'application/zip'


class RecentSubmissionsFeed(SubmissionsFeed):
    title = _('MDN recent demos')
    subtitle = _('Demos recently submitted to MDN')

    def items(self):
        submissions = (Submission.objects.exclude(hidden=True)
                                         .order_by('-modified')[:MAX_FEED_ITEMS])
        return submissions


class FeaturedSubmissionsFeed(SubmissionsFeed):
    title = _('MDN featured demos')
    subtitle = _('Demos featured on MDN')

    def items(self):
        submissions = Submission.objects.all_sorted(
            sort='recentfeatured',
            max=MAX_FEED_ITEMS
        )
        return submissions


class TagSubmissionsFeed(SubmissionsFeed):

    def get_object(self, request, format, tag):
        super(TagSubmissionsFeed, self).get_object(request, format)
        if tag in TAG_DESCRIPTIONS:
            self.title = _('MDN demos tagged %s') % TAG_DESCRIPTIONS[tag]['title']
            self.subtitle = TAG_DESCRIPTIONS[tag]['description']
        else:
            self.title = _('MDN demos tagged "%s"') % tag
            self.subtitle = None
        return tag

    def items(self, tag):
        submissions = (Submission.objects.filter(taggit_tags__name__in=[tag])
                                         .exclude(hidden=True)
                                         .order_by('-modified')[:MAX_FEED_ITEMS])
        return submissions


class ProfileSubmissionsFeed(SubmissionsFeed):

    def get_object(self, request, format, username):
        super(ProfileSubmissionsFeed, self).get_object(request, format)
        user = get_object_or_404(get_user_model(), username=username)
        self.title = _("%s's MDN demos") % user.username
        return user

    def items(self, user):
        return (Submission.objects.filter(creator=user)
                                  .exclude(hidden=True)
                                  .order_by('-modified')[:MAX_FEED_ITEMS])


class SearchSubmissionsFeed(SubmissionsFeed):

    def get_object(self, request, format):
        query_string = request.GET.get('q', '')
        super(SearchSubmissionsFeed, self).get_object(request, format)
        self.title = _('MDN demo search for "%s"') % query_string
        self.subtitle = _('Search results for demo submissions matching "%s"') % query_string
        return query_string

    def items(self, query_string):
        submissions = Submission.objects.search(query_string, 'created')\
            .exclude(hidden=True)\
            .order_by('-modified').all()[:MAX_FEED_ITEMS]
        return submissions

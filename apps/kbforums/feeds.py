from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed
from django.utils.html import strip_tags, escape

from tower import ugettext as _

import forums as constants
from kbforums.models import Thread
from wiki.models import Document


class ThreadsFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, document_slug):
        return get_object_or_404(Document,
                                 slug=document_slug,
                                 locale=request.locale)

    def title(self, document):
        return _('Recently updated threads about %s') % document.title

    def link(self, document):
        return document.get_absolute_url()

    def items(self, document):
        return document.thread_set.order_by(
                '-last_post__created')[:constants.THREADS_PER_PAGE]

    def item_title(self, item):
        return item.title

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created


class PostsFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, document_slug, thread_id):
        doc = get_object_or_404(Document,
                                slug=document_slug,
                                locale=request.locale)
        return get_object_or_404(Thread, pk=thread_id, document=doc)

    def title(self, thread):
        return _('Recent posts in %s') % thread.title

    def link(self, thread):
        return thread.get_absolute_url()

    def description(self, thread):
        return self.title(thread)

    def items(self, thread):
        return thread.post_set.order_by('-created')

    def item_title(self, item):
        return strip_tags(item.content_parsed)[:100]

    def item_description(self, item):
        return escape(item.content_parsed)

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created

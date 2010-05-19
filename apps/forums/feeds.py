from django.shortcuts import get_object_or_404

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from tower import ugettext as _

from .models import Forum, Thread
import forums as constants


class ThreadsFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, forum_slug):
        return get_object_or_404(Forum, slug=forum_slug)

    def title(self, forum):
        return _('Recently updated threads in %s') % forum.name

    def link(self, forum):
        return forum.get_absolute_url()

    def description(self, forum):
        return forum.description

    def items(self, forum):
        return forum.thread_set.order_by(
                '-last_post__created')[:constants.THREADS_PER_PAGE]


class PostsFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, forum_slug, thread_id):
        return get_object_or_404(Thread, pk=thread_id)

    def title(self, thread):
        return _('Recent posts in %s') % thread.title

    def link(self, thread):
        return thread.get_absolute_url()

    def description(self, thread):
        return self.title(thread)

    def items(self, thread):
        return thread.post_set.order_by('-created')

"""
migrate_forum: a management command to migrate SUMO's tiki forum data over
to our new forums app.

IMPORTANT: The migration attempts to keep the same thread ids (for easy
URL redirects) and hence assumes all those thread ids are available in the
forums app's thread table.

Goes through each forum (specified by forum_id), creates all threads and,
for each thread, creates all posts belonging to it.

Uses a markup converter to transform TikiWiki syntax to MediaWiki syntax.
"""
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags

from forums.models import Forum, Thread, Post
from sumo.models import Forum as TikiForum
from sumo.converter import TikiMarkupConverter
from sumo.migration_utils import get_django_user, fetch_threads, fetch_posts


# Converts TikiWiki syntax to MediaWiki syntax
converter = TikiMarkupConverter()


def create_post(thread, tiki_post):
    """Create a post in `thread` from a Tiki post."""
    author = get_django_user(tiki_post)
    created = datetime.fromtimestamp(tiki_post.commentDate)
    post_content = converter.convert(tiki_post.data)

    return Post.objects.create(
        thread=thread, author=author, content=post_content,
        created=created, updated=created, updated_by=author)


def create_thread(forum, tiki_thread):
    """
    Create a thread in `forum` from a Tiki thread.

    Keeps the same thread id. Also creates the first post in that thread.
    """
    creator = get_django_user(tiki_thread)
    created = datetime.fromtimestamp(tiki_thread.commentDate)

    is_locked = (tiki_thread.type == 'l' or tiki_thread.type == 'a')
    is_sticky = (tiki_thread.type == 's' or tiki_thread.type == 'a')

    thread = Thread.objects.create(
        id=tiki_thread.threadId, title=tiki_thread.title, creator=creator,
        is_locked=is_locked, is_sticky=is_sticky, forum=forum,
        created=created)

    # now create the thread's first post
    thread.last_post = create_post(thread, tiki_thread)

    return thread


def create_forum(tiki_forum):
    """Creates a forum given a Tiki forum."""
    forum_slug = slugify(tiki_forum.name)
    clean_description = strip_tags(tiki_forum.description)
    try:
        forum = Forum.objects.create(
            name=tiki_forum.name, slug=forum_slug,
            description=clean_description)
    except IntegrityError:
        raise CommandError(
            'A forum with name "%s" or slug "%s" already exists.' %
            (tiki_forum.name, forum_slug))

    return forum


class Command(BaseCommand):
    args = '<forum_id forum_id ...>'
    help = 'Migrate data from specified Tiki forum(s). Please not forum 1.'
    max_threads = 100  # Max number of threads to store at any time
    max_posts = 100    # Max number of posts to store at any time

    def handle(self, *args, **options):
        # Requires at least one forum_id
        if not args:
            raise CommandError('Usage: ./manage.py migrate_forum %s' %
                               self.args)

        for forum_id in args:
            try:
                tiki_forum = TikiForum.objects.get(pk=int(forum_id))
            except TikiForum.DoesNotExist:
                raise CommandError('Forum "%s" does not exist' % forum_id)

            forum = create_forum(tiki_forum)

            if options['verbosity'] > 0:
                print ('Starting migration for forum "%s" (%s)' %
                       (tiki_forum.name, forum_id))

            if options['verbosity'] > 0:
                print 'Created forum "%s" (%s)...' % (forum.name, forum.id)

            # ... then create the threads
            thread_offset = 0
            threads = fetch_threads(tiki_forum, self.max_threads,
                                    thread_offset)
            thread_i = 0
            while threads:
                try:
                    tiki_thread = threads[thread_i]
                except IndexError:
                    # we're done with this list, next!
                    thread_offset = thread_offset + self.max_threads
                    threads = fetch_threads(tiki_forum, self.max_threads,
                                            thread_offset)
                    thread_i = 0
                    continue

                if options['verbosity'] > 1:
                    print 'Processing thread %s...' % tiki_thread.threadId
                thread = create_thread(forum, tiki_thread)

                # keep track of the last_post
                last_post = thread.last_post

                # ... then create its posts
                post_offset = 0
                posts = fetch_posts(tiki_thread, self.max_posts, post_offset)
                post_i = 0
                while posts:
                    try:
                        tiki_post = posts[post_i]
                    except IndexError:
                        post_offset = post_offset + self.max_posts
                        posts = fetch_posts(tiki_thread, self.max_posts,
                                            post_offset)
                        post_i = 0
                        continue

                    if options['verbosity'] > 2:
                        print ('Processing post %s for thread %s...' %
                           (tiki_post.threadId, tiki_post.parentId))
                    post = create_post(thread, tiki_post)
                    post_i = post_i + 1

                    # if this post is newer than the last_post, update it
                    if post.created > last_post.created:
                        last_post = post

                thread.last_post = last_post
                thread.save()

                thread_i = thread_i + 1

            if options['verbosity'] > 0:
                print ('Successfully migrated posts in forum "%s" (%s)' %
                       (tiki_forum.name, forum_id))

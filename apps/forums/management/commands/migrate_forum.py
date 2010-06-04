from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags

from forums.models import Forum, Thread, Post
from sumo.models import (Forum as TikiForum, ForumThread as TikiThread,
                         TikiUser)
from sumo.converter import TikiMarkupConverter


class Command(BaseCommand):
    args = '<forum_id forum_id ...>'
    help = 'Migrate data from specified Tiki forum(s). Please not forum 1.'
    max_threads = 100  # Max number of threads to store at any time
    max_posts = 100    # Max number of posts to store at any time

    thread_offset = 0
    threads = None
    post_offset = 0
    posts = None

    # Converts TikiWiki syntax to MediaWiki syntax
    converter = TikiMarkupConverter()

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

            print ('Starting migration for forum "%s" (%s)' %
                   (tiki_forum.name, forum_id))

            # First create the forum...
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

            print 'Created forum "%s" (%s)...' % (forum.name, forum.id)

            # ... then create the threads
            self.fetch_threads(tiki_forum)
            thread_i = 0
            while self.threads:
                try:
                    tiki_thread = self.threads[thread_i]
                except IndexError:
                    # we're done with this list, next!
                    self.fetch_threads(tiki_forum)
                    thread_i = 0
                    continue

                print 'Processing thread %s...' % tiki_thread.threadId
                thread = self.create_thread(forum, tiki_thread)

                # ... then create its posts
                self.post_offset = 0
                self.fetch_posts(tiki_thread)
                post_i = 0
                while self.posts:
                    try:
                        tiki_post = self.posts[post_i]
                    except IndexError:
                        self.fetch_posts(tiki_thread)
                        post_i = 0
                        continue

                    print ('Processing post %s for thread %s...' %
                           (tiki_post.threadId, tiki_post.parentId))
                    self.create_post(thread, tiki_post)
                    post_i = post_i + 1

                # Free up memory
                self.posts = []

                thread_i = thread_i + 1

            print ('Successfully migrated posts in forum "%s" (%s)' %
                   (tiki_forum.name, forum_id))
            # Clean up
            self.thread_offset = 0
            self.threads = None

    def fetch_threads(self, tiki_forum):
        """Gets the next max_threads for tiki_forum.forumId."""
        # slice and dice
        start = self.thread_offset
        end = self.thread_offset + self.max_threads

        self.threads = TikiThread.objects.filter(
            objectType='forum', object=tiki_forum.forumId,
            parentId=0)[start:end]

        # advance
        self.thread_offset = end

    def fetch_posts(self, tiki_thread):
        """Gets the next max_posts for tiki_thread.threadId."""
        # slice and dice
        start = self.post_offset
        end = self.post_offset + self.max_posts

        self.posts = TikiThread.objects.filter(
            objectType='forum', parentId=tiki_thread.threadId)[start:end]

        # advance
        self.post_offset = end

    def create_thread(self, forum, tiki_thread):
        """
        Create a thread in `forum` from a Tiki thread.

        Keeps the same thread id. Also creates the first post in that thread.
        """
        creator = self.get_django_user(tiki_thread)

        is_locked = (tiki_thread.type == 'l')
        is_sticky = (tiki_thread.type == 's')

        thread = Thread.objects.create(
            id=tiki_thread.threadId, title=tiki_thread.title, creator=creator,
            is_locked=is_locked, is_sticky=is_sticky, forum=forum)

        # now create the thread's first post
        self.create_post(thread, tiki_thread)

        return thread

    def create_post(self, thread, tiki_post):
        """Create a post in `thread` from a Tiki post."""
        author = self.get_django_user(tiki_post)
        post_content = self.converter.convert(tiki_post.data)

        return Post.objects.create(
            thread=thread, author=author, content=post_content)

    def get_django_user(self, tiki_thread):
        """Get the django user for this thread's username."""
        try:
            user = User.objects.get(username=tiki_thread.userName)
        except User.DoesNotExist:
            # Assign a dummy user to this thread
            user = self.get_fake_user()
            print ('Using fake user for thread %s, could not find "%s"' %
                   (tiki_thread.threadId, tiki_thread.userName))

        return user

    def get_fake_user(self):
        """Get a fake user. If one does not exist, create it."""
        try:
            return User.objects.get(username='FakeUser')
        except User.DoesNotExist:
            tiki_user = TikiUser.objects.create(
                login='FakeUser', password='md5$pass', hash='md5$hash')
            return User.objects.create(
                id=tiki_user.userId, username='FakeUser')

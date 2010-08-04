"""
migrate_questions: a management command to migrate SUMO's tiki support forum
data over to our new questions app.

IMPORTANT: The migration attempts to keep the same ids (question.id) for easy
URL redirects, and hence assumes all those question ids are available in the
questions app's question table. I.e. this command will fail if a question
already exists with the same id in both tables.

Goes through each question and creates all answers belonging to it. Also
migrates the question metadata.

Uses a markup converter to transform TikiWiki syntax to MediaWiki syntax.
"""
from datetime import datetime
import re

from django.core.management.base import BaseCommand, CommandError

from multidb.pinning import pin_this_thread

from questions.models import Question, Answer, CONFIRMED
from questions.question_config import products
from sumo.models import (Forum as TikiForum,
                         ForumThreadMetaData as TikiThreadMetaData)
from sumo.converter import TikiMarkupConverter
from sumo.migration_utils import (get_django_user, fetch_threads, fetch_posts,
                                  get_firefox_version, get_OS)


# Converts TikiWiki syntax to MediaWiki syntax
converter = TikiMarkupConverter()


def create_answer(question, tiki_post, tiki_thread):
    """Create an answer to a question from a Tiki post."""
    creator = get_django_user(tiki_post)
    created = datetime.fromtimestamp(tiki_post.commentDate)
    content = converter.convert(tiki_post.data)

    ans = Answer(question=question, creator=creator, content=content,
                 created=created, updated=created)
    ans.save(no_update=True, no_notify=True)  # don't send a reply notification

    # Set answer as solution
    if tiki_post.type == 'o' and tiki_thread.type == 'o':
        question.solution = ans

    return ans


patterns_clean = (
    '^== Troubleshooting information ==\n(.*?)^==',
    '^== Issue ==\n(.*?)^==',
    '^== Firefox version ==\n(.*?)^==',
    '^== Operating system ==\n(.*?)^==',
    '^== User Agent ==\n(.*?)^==',
    '^== Plugins installed ==\n(.*)',
    '^== Description ==\n',
)

compiled_patterns_clean = []
for pattern in patterns_clean:
    compiled_patterns_clean.append(re.compile(
        pattern, re.MULTILINE | re.DOTALL | re.IGNORECASE))

# Description has a different replace rule, so keep it separate
compiled_pattern_description = compiled_patterns_clean.pop()


def clean_question_content(question):
    """Cleans everything after troubleshooting in old threads (user agent, OS,
    etc.) and adds troubleshooting as metadata.

    """

    m = compiled_patterns_clean[0].search(question.content)
    if m:
        troubleshooting = m.group(1)

    for p in compiled_patterns_clean:
        question.content = p.sub('==', question.content)

    question.content = compiled_pattern_description.sub('', question.content)

    question.content = question.content.rstrip(' \t\r\n=')
    question.save(no_update=True)

    if m:
        question.add_metadata(troubleshooting=troubleshooting)


def update_question_updated_date(question):
    """Update the question's updated date and set it to that of the most recent
    answer.

    """
    if question.last_answer:
        question.updated = question.last_answer.updated
        question.save(no_update=True)


def create_question(tiki_thread):
    """
    Create a question from a Tiki thread.

    Keeps the same question id.
    """
    creator = get_django_user(tiki_thread)
    created = datetime.fromtimestamp(tiki_thread.commentDate)
    content = converter.convert(tiki_thread.data)

    is_locked = (tiki_thread.type == 'l' or tiki_thread.type == 'a')

    question = Question(
        id=tiki_thread.threadId, title=tiki_thread.title, creator=creator,
        is_locked=is_locked, status=CONFIRMED, confirmation_id='',
        created=created, updated=created, content=content)

    return question


def create_question_metadata(question):
    """
    Look up metadata in the question and tiki_comments_metadata and create and
    attach it to the QuestionMetaData model.
    """
    dirty_content = question.content

    clean_question_content(question)
    metadata = TikiThreadMetaData.objects.filter(threadId=question.id)

    for meta in metadata:
        if meta.name == 'useragent':
            question.add_metadata(useragent=meta.value)
            # Look for OS and version
            os_ = get_OS(meta.value)
            if os_:
                question.add_metadata(os=os_)
            version = get_firefox_version(meta.value)
            if version:
                question.add_metadata(ff_version=version)

        elif meta.name == 'plugins':
            question.add_metadata(plugins=meta.value)

    # Potential remaining metadata: sites_affected, troubleshooting

    # Setting all questions to the desktop product
    question.add_metadata(product='desktop')

    # Set category based on the content
    cats = products['desktop']['categories']
    for c_name in cats:
        if unicode(cats[c_name]['name']) in dirty_content:
            question.add_metadata(category=c_name)
            break

    # Auto-tag this question after the metadata is added
    question.auto_tag()


class Command(BaseCommand):
    forum_id = 1
    help = 'Migrate data from forum 1.'
    max_threads = 100  # Max number of threads to store at any time
    max_posts = 100    # Max number of posts to store at any time

    max_total_threads = 15000  # Max number of threads to migrate

    def handle(self, *args, **options):
        pin_this_thread()

        # Requires at least one forum_id
        if args:
            raise CommandError('Usage: ./manage.py migrate_questions')

        try:
            tiki_forum = TikiForum.objects.get(pk=self.forum_id)
        except TikiForum.DoesNotExist:
            raise CommandError('Forum "%s" does not exist' % self.forum_id)

        if options['verbosity'] > 0:
            print ('Starting migration for forum "%s" (%s)' %
                   (tiki_forum.name, self.forum_id))

        # Create the questions
        thread_offset = 0
        threads = fetch_threads(tiki_forum, self.max_threads,
                                thread_offset)
        thread_counter = self.max_threads
        thread_i = 0
        while threads and thread_counter <= self.max_total_threads:
            try:
                tiki_thread = threads[thread_i]
            except IndexError:
                # we're done with this list, next!
                thread_offset = thread_offset + self.max_threads
                threads = fetch_threads(tiki_forum, self.max_threads,
                                        thread_offset)
                thread_counter += self.max_threads
                thread_i = 0
                continue

            if options['verbosity'] > 1:
                print 'Processing thread %s...' % tiki_thread.threadId

            # Create question..
            question = create_question(tiki_thread)
            create_question_metadata(question)

            # ... then create its answers
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

                # Create answer
                create_answer(question, tiki_post, tiki_thread)
                post_i = post_i + 1

            # Now that all answers have been migrated, update the question's
            # updated date
            update_question_updated_date(question)
            thread_i = thread_i + 1

        if options['verbosity'] > 0:
            print ('Successfully migrated posts in forum "%s" (%s)' %
                   (tiki_forum.name, self.forum_id))

        if options['verbosity'] > 0 and \
            thread_counter >= self.max_total_threads:
            print ('Reached maximum number of threads to migrate ' +
                   '(%s) and stopped.' % self.max_total_threads)

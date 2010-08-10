from datetime import datetime

from django.test import TestCase

from nose.tools import eq_

from questions.management.commands.migrate_questions import (
    create_question, create_answer, update_question_updated_date,
    clean_question_content, create_question_metadata,
    post_reply_in_old_thread)
from questions.models import CONFIRMED
from sumo.models import ForumThread as TikiThread


class MigrateManualTestCase(TestCase):
    fixtures = ['users.json', 'tikiusers.json', 'questions_tiki.json']

    def test_question_basic(self):
        t = TikiThread.objects.filter(threadId=727433)[0]
        q = create_question(t)
        eq_(t.title, q.title)
        eq_('AnonymousUser', q.creator.username)
        eq_(False, q.is_locked)
        eq_(CONFIRMED, q.status)
        eq_('2010-07-15 21:52:03', str(q.created))
        self.assertNotEquals(0, len(q.content))

    def test_question_reply_to_thread(self):
        """When a question is created, the corresponding Tiki thread is replied
        to."""
        t = TikiThread.objects.filter(threadId=714290)[0]
        q = create_question(t)
        q.save(no_update=True)
        post_reply_in_old_thread(t, q)
        r = TikiThread.objects.filter(parentId=714290) \
                .order_by('-commentDate')[0]
        eq_('Comment on thread %s' % t.threadId, r.title)

    def test_question_locked(self):
        """Type 'l' are locked questions."""
        t = TikiThread.objects.filter(type='l', parentId=0)[0]
        q = create_question(t)
        eq_(True, q.is_locked)

    def test_question_announce(self):
        """Announcements (type 'a') are locked questions."""
        t = TikiThread.objects.filter(type='a', parentId=0)[0]
        q = create_question(t)
        eq_(True, q.is_locked)

    def test_question_solved(self):
        """Question is marked as solved when type is 'o'."""
        t = TikiThread.objects.filter(type='o', parentId=0)[0]
        q = create_question(t)
        q.save(no_update=True)

        p = TikiThread.objects.filter(type='o', parentId=t.threadId)[0]
        a = create_answer(q, p, t)
        # Check created date is the same as the tiki equivalent
        eq_(datetime.fromtimestamp(p.commentDate), q.solution.created)
        # And then the newly created answer is a solution
        eq_(a, q.solution)

    def test_question_updated_date_add_answer(self):
        """Question's updated date is not affected when adding an answer."""
        t = TikiThread.objects.filter(type='o', parentId=0)[0]
        q = create_question(t)
        q.save(no_update=True)

        p = TikiThread.objects.filter(type='o', parentId=t.threadId)[0]
        create_answer(q, p, t)
        # Check created date is the same as the tiki equivalent
        eq_(datetime.fromtimestamp(t.commentDate), q.updated)

    def test_question_updated_date_clean_content(self):
        """Cleaning the question's content does not affect its updated date."""
        t = TikiThread.objects.filter(threadId=728030)[0]
        q = create_question(t)

        clean_question_content(q)
        eq_(datetime.fromtimestamp(t.commentDate), q.updated)

    def test_update_question_updated_date(self):
        """A question's updated date is set twice: on creation and when calling
        `update_question_updated_date`

        """
        t = TikiThread.objects.filter(type='o', parentId=0)[0]
        q = create_question(t)
        eq_(datetime.fromtimestamp(t.commentDate), q.updated)
        q.save(no_update=True)

        p = TikiThread.objects.filter(type='o', parentId=t.threadId)[0]
        create_answer(q, p, t)
        # Updated date is unchanged
        eq_(datetime.fromtimestamp(t.commentDate), q.updated)

        # Now call the function to be tested
        update_question_updated_date(q)
        # Check created date is the same as the tiki equivalent
        eq_(datetime.fromtimestamp(p.commentDate), q.updated)

    def test_question_metadata(self):
        """Question metadata is populated."""
        t = TikiThread.objects.filter(threadId=727433)[0]
        q = create_question(t)

        create_question_metadata(q)

        eq_('home', q.metadata_set.filter(name='product')[0].value)

    def test_clean_question_content(self):
        """Question content is cleaned up."""
        t = TikiThread.objects.filter(threadId=728030)[0]
        q = create_question(t)

        clean_question_content(q)

        # Check content is clean
        eq_(True, q.content.startswith('Upon installation on my 3G'))
        eq_(True, q.content.endswith('Firefox opened'))

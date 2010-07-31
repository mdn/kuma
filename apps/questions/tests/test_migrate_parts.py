from datetime import datetime

from django.test import TestCase

from nose.tools import eq_

from questions.management.commands.migrate_questions import (
    create_question, create_answer,
    _clean_question_content, create_question_metadata)
from questions.models import CONFIRMED
from sumo.models import ForumThread as TikiThread


class MigrateManualTestCase(TestCase):
    fixtures = ['users.json', 'tikiusers.json', 'questions_tiki.json']

    def test_question_basic(self):
        t = TikiThread.objects.filter(threadId=737114)[0]
        q = create_question(t)
        eq_(737114, q.id)
        eq_(t.title, q.title)
        eq_('pcraciunoiu', q.creator.username)
        eq_(False, q.is_locked)
        eq_(CONFIRMED, q.status)
        eq_('', q.confirmation_id)
        eq_('2010-07-25 23:05:00', str(q.created))
        self.assertNotEquals(0, len(q.content))

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
        q.save()

        p = TikiThread.objects.filter(type='o', parentId=t.threadId)[0]
        a = create_answer(q, p, t)
        # Check created date is the same as the tiki equivalent
        eq_(datetime.fromtimestamp(p.commentDate), q.solution.created)
        # And then the newly created answer is a solution
        eq_(a, q.solution)

    def test_question_metadata(self):
        """Question metadata is populated."""
        t = TikiThread.objects.filter(threadId=736751)[0]
        q = create_question(t)

        create_question_metadata(q)
        q.save()

        eq_('d3', q.metadata_set.filter(name='category')[0].value)
        eq_('desktop', q.metadata_set.filter(name='product')[0].value)
        eq_('3.6.6', q.metadata_set.filter(name='ff_version')[0].value)
        eq_(1, q.metadata_set.filter(name='useragent').count())
        eq_(1, q.metadata_set.filter(name='plugins').count())
        eq_(1, q.metadata_set.filter(name='troubleshooting').count())

    def test_clean_question_content(self):
        """Question content is cleaned up and metadata for troubleshooting is
        set accordingly.

        """
        t = TikiThread.objects.filter(threadId=736751)[0]
        q = create_question(t)

        _clean_question_content(q)

        # First check content is clean
        eq_(True, q.content.startswith('I recently had'))
        eq_(True, q.content.endswith('have.'))

        # Now check metadata for troubleshooting
        eq_(1, q.metadata_set.filter(name='troubleshooting').count())
        eq_(u'ADP 1.2.1\nJava Console 6.0.2.1\nMicrosoft.NET Framework ' +
                'Assistant 1.2.1\n\n',
            q.metadata_set.filter(name='troubleshooting')[0].value)

from django.db.models.signals import post_save

from nose.tools import eq_

from questions.models import Question, QuestionVote, send_vote_update_task
from questions.tasks import update_question_vote_chunk
from sumo.tests import TestCase


class QuestionVoteTestCase(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        post_save.disconnect(send_vote_update_task, sender=QuestionVote)

    def tearDown(self):
        post_save.connect(send_vote_update_task, sender=QuestionVote)

    def test_update_question_vote_chunk(self):
        # Reset the num_votes_past_week counts, I suspect the data gets
        # loaded before I disconnect the signal and they get zeroed out.
        q = Question.objects.get(pk=3)
        q.num_votes_past_week = q.num_votes
        q.save()

        q = Question.objects.get(pk=2)
        q.num_votes_past_week = q.num_votes
        q.save()

        # Actually test the task.
        q1 = Question.objects.all().order_by('-num_votes_past_week')
        eq_(3, q1[0].pk)

        QuestionVote.objects.create(question=q1[1])
        q2 = Question.uncached.all().order_by('-num_votes_past_week')
        eq_(3, q2[0].pk)

        update_question_vote_chunk([q.pk for q in q1])
        q3 = Question.uncached.all().order_by('-num_votes_past_week')
        eq_(2, q3[0].pk)

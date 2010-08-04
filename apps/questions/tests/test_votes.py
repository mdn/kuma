from nose.tools import eq_

from questions.models import Question, QuestionVote
from questions.tests import TestCaseBase
from questions.cron import update_weekly_votes


class TestVotes(TestCaseBase):
    """Test QuestionVote counting and cron job."""

    def test_vote_updates_count(self):
        q = Question.objects.all()[0]
        eq_(0, q.num_votes_past_week)

        vote = QuestionVote(question=q, anonymous_id='abc123')
        vote.save()
        eq_(1, q.num_votes_past_week)

    def test_cron_updates_counts(self):
        q = Question.objects.all()[0]
        eq_(0, q.num_votes_past_week)

        vote = QuestionVote(question=q, anonymous_id='abc123')
        vote.save()
        q.num_votes_past_week = 0
        q.save()

        update_weekly_votes()

        q = Question.objects.get(pk=q.pk)
        eq_(1, q.num_votes_past_week)

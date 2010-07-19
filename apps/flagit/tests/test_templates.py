from nose.tools import eq_
from pyquery import PyQuery as pq

from questions.models import Answer
from flagit.tests import TestCaseBase, post, get
from flagit.models import FlaggedObject


class FlaggedQueueTestCase(TestCaseBase):
    """Test the flagit queue."""
    def setUp(self):
        super(FlaggedQueueTestCase, self).setUp()
        self.client.login(username='admin', password='testpass')

    def tearDown(self):
        super(FlaggedQueueTestCase, self).tearDown()
        self.client.logout()

    def test_queue(self):
        # Flag all answers
        num_answers = Answer.objects.count()
        for a in Answer.objects.all():
            f = FlaggedObject(content_object=a, reason='spam',
                                 creator_id=118577)
            f.save()

        # Verify number of flagged objects
        response = get(self.client, 'flagit.queue')
        doc = pq(response.content)
        eq_(num_answers, len(doc('#flagged-queue li')))

        # Reject one flag
        flag = FlaggedObject.objects.all()[0]
        response = post(self.client, 'flagit.update',
                        {'status': 2},
                        args=[flag.id])
        doc = pq(response.content)
        eq_(num_answers - 1, len(doc('#flagged-queue li')))

from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from flagit.tests import TestCaseBase
from flagit.models import FlaggedObject
from questions.models import Question
from sumo.tests import post


class FlagTestCase(TestCaseBase):
    """Test the flag view."""
    def setUp(self):
        super(FlagTestCase, self).setUp()
        self.client.login(username='jsocol', password='testpass')
        self.question = Question.objects.all()[0]

    def tearDown(self):
        super(FlagTestCase, self).tearDown()
        self.client.logout()

    def test_flag(self):
        """Flag a question."""
        d = {'content_type': ContentType.objects.get_for_model(Question).id,
             'object_id': self.question.id,
             'reason': 'spam',
             'next': self.question.get_absolute_url()}
        post(self.client, 'flagit.flag', d)
        eq_(1, FlaggedObject.objects.count())

        flag = FlaggedObject.objects.all()[0]
        eq_('jsocol', flag.creator.username)
        eq_('spam', flag.reason)
        eq_(self.question, flag.content_object)

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

import mock

from questions.tasks import build_answer_notification
from . import TestCaseBase
import notifications.tasks
from questions.models import Question, Answer


EMAIL_CONTENT = (
    """

Answer to question: Lorem ipsum dolor sit amet?

pcraciunoiu has posted an answer to the question 
Lorem ipsum dolor sit amet?.

========

Just an answer.

========

To view this answer on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/questions/1#answer-1
""",
    """

Answer to question: Lorem ipsum dolor sit amet?

jsocol has posted an answer to the question 
Lorem ipsum dolor sit amet?.

========

an answer

========

To view this answer on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/questions/1#answer-%s
""",
)


class NotificationTestCase(TestCaseBase):
    """Test that notifications get sent."""

    def setUp(self):
        super(NotificationTestCase, self).setUp()

        self.ct = ContentType.objects.get_for_model(Question)

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_notification(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        answer = Answer.objects.get(pk=1)
        build_answer_notification(answer)

        delay.assert_called_with(
            self.ct, answer.question.id,
            u'New answer to: %s' % answer.question.title,
            EMAIL_CONTENT[0],
            (u'user47963@nowhere',))

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_notification_on_save(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        q = Question.objects.get(pk=1)
        user = User.objects.get(pk=118533)
        a = q.answers.create(creator=user, content='an answer')
        a.save()

        delay.assert_called_with(
            self.ct, q.pk,
            u'New answer to: %s' % q.title,
            EMAIL_CONTENT[1] % a.pk,
            (u'user118533@nowhere',))

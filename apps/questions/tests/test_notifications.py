from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

import mock

from questions.tasks import (build_answer_notification,
                             build_solution_notification)
from . import TestCaseBase, post
import notifications.tasks
from questions.models import Question, Answer


EMAIL_CONTENT = (
    """

Answer to question: Lorem ipsum dolor sit amet?

pcraciunoiu has posted an answer to the question 
Lorem ipsum dolor sit amet?.

========

An answer & stuff.

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
    """

Solution to question: Lorem ipsum dolor sit amet?

jsocol has accepted a solution to the question 
Lorem ipsum dolor sit amet?.

========

An answer & stuff.

========

To view the solution on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/questions/1#answer-1
""",
)


class NotificationTestCase(TestCaseBase):
    """Test that notifications get sent."""

    def setUp(self):
        super(NotificationTestCase, self).setUp()

        self.ct = ContentType.objects.get_for_model(Question)

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_answer_notification(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        answer = Answer.objects.get(pk=1)
        build_answer_notification(answer)

        delay.assert_called_with(
            self.ct, answer.question.id,
            u'New answer to: %s' % answer.question.title,
            EMAIL_CONTENT[0],
            (u'user47963@nowhere',),
            'reply')

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_solution_notification(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        answer = Answer.objects.get(pk=1)
        question = answer.question
        question.solution = answer
        question.save()
        build_solution_notification(question)

        delay.assert_called_with(
            self.ct, question.id,
            u'Solution to: %s' % question.title,
            EMAIL_CONTENT[2],
            (u'user118533@nowhere',),
            'solution')

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_solution_notification_deleted(self, get_current, delay):
        """Calling build_solution_notification should not query the
        questions_question table.

        This test attempts to simulate the replication lag presumed to cause
        bug 585029.

        """
        get_current.return_value.domain = 'testserver'

        answer = Answer.objects.get(pk=1)
        question = Question.objects.get(pk=1)
        question.solution = answer
        question.save()

        # Delete the question, pretend it hasn't been replicated yet
        Question.objects.get(pk=question.pk).delete()

        build_solution_notification(question)

        delay.assert_called_with(
            self.ct, question.id,
            u'Solution to: %s' % question.title,
            EMAIL_CONTENT[2],
            (u'user118533@nowhere',),
            'solution')

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
            (u'user118533@nowhere',),
            'reply')

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_notification_on_solution(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        answer = Answer.objects.get(pk=1)
        question = answer.question
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'questions.solution', args=[question.id, answer.id])

        delay.assert_called_with(
            self.ct, question.id,
            u'Solution to: %s' % question.title,
            EMAIL_CONTENT[2],
            (u'user118533@nowhere',),
            'solution')

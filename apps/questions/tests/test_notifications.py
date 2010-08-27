from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

import mock

from questions.models import Question, Answer
from questions.tasks import (build_answer_notification,
                             build_solution_notification)
from . import TestCaseBase
import notifications.tasks
from questions.models import Question, Answer
from sumo.tests import post


# These mails are generated using reverse() calls, which return different
# results depending on whether a request is being processed at the time. This
# is because reverse() depends on a thread-local var which is set/unset at
# request boundaries by LocaleURLMiddleware. While a request is in progress,
# reverse() prepends a locale code; otherwise, it doesn't. Thus, when making a
# mock request that fires off a celery task that generates one of these emails,
# expect a locale in reverse()d URLs. When firing off a celery task outside the
# scope of a request, expect none. For example, when firing an email-building
# task from within a POST request, compare the result with
# SOLUTION_EMAIL_INSIDE_REQUEST. When calling the task directly from the test,
# compare with SOLUTION_EMAIL_OUTSIDE_REQUEST.
#
# In production, with CELERY_ALWAYS_EAGER=False, celery tasks run in a
# different interpreter (with no access to the thread-local), so reverse() will
# never prepend a locale code unless passed force_locale=True. Thus, these
# test-emails with locale prefixes are not identical to the ones sent in
# production.
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

https://testserver/questions/1#answer-1
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

https://testserver/questions/1#answer-%s
""")
SOLUTION_EMAIL_INSIDE_REQUEST, SOLUTION_EMAIL_OUTSIDE_REQUEST = [
    """

Solution to question: Lorem ipsum dolor sit amet?

jsocol has accepted a solution to the question 
Lorem ipsum dolor sit amet?.

========

An answer & stuff.

========

To view the solution on the site, click the following link, or
paste it into your browser's location bar:

https://testserver%s/questions/1#answer-1
""" % s for s in ['/en-US', '']]


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
            SOLUTION_EMAIL_OUTSIDE_REQUEST,
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
            SOLUTION_EMAIL_OUTSIDE_REQUEST,
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
            SOLUTION_EMAIL_INSIDE_REQUEST,
            (u'user118533@nowhere',),
            'solution')

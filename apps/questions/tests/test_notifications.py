from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.core import mail

from nose.tools import eq_
import mock

from questions.events import QuestionReplyEvent, QuestionSolvedEvent
from questions.models import Question, Answer
from questions.tests import TestCaseBase
from sumo.tests import post, attrs_eq
from users.tests import user


# These mails are generated using reverse() calls, which return different
# results depending on whether a request is being processed at the time. This
# is because reverse() depends on a thread-local var which is set/unset at
# request boundaries by LocaleURLMiddleware. While a request is in progress,
# reverse() prepends a locale code; otherwise, it doesn't. Thus, when making a
# mock request that fires off a celery task that generates one of these emails,
# expect a locale in reverse()d URLs. When firing off a celery task outside the
# scope of a request, expect none.
#
# In production, with CELERY_ALWAYS_EAGER=False, celery tasks run in a
# different interpreter (with no access to the thread-local), so reverse() will
# never prepend a locale code unless passed force_locale=True. Thus, these
# test-emails with locale prefixes are not identical to the ones sent in
# production.
ANSWER_EMAIL_INSIDE_REQUEST = """

Answer to question: Lorem ipsum dolor sit amet?

jsocol has posted an answer to the question 
Lorem ipsum dolor sit amet?.

========

an answer

========

To view this answer on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/questions/1#answer-%s
"""
SOLUTION_EMAIL_INSIDE_REQUEST = """

Solution to question: Lorem ipsum dolor sit amet?

jsocol has accepted a solution to the question 
Lorem ipsum dolor sit amet?.

========

An answer & stuff.

========

To view the solution on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/questions/1#answer-%s
"""


class NotificationsTests(TestCaseBase):
    """Test that notifications get sent."""

    def setUp(self):
        super(NotificationsTests, self).setUp()

    @mock.patch_object(QuestionReplyEvent, 'fire')
    def test_fire_on_new_answer(self, fire):
        """The event fires when a new answer is saved."""
        question = Question.objects.all()[0]
        Answer.objects.create(question=question, creator=user(save=True))

        assert fire.called

    @mock.patch_object(QuestionSolvedEvent, 'fire')
    def test_fire_on_solution(self, fire):
        """The event also fires when an answer is marked as a solution."""
        answer = Answer.objects.get(pk=1)
        question = answer.question
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'questions.solution', args=[question.id, answer.id])

        assert fire.called

    def _toggle_watch_question(self, event_type, turn_on=True):
        """Helper to watch/unwatch a question. Fails if called twice with
        the same turn_on value."""
        question = Question.objects.all()[0]
        self.client.login(username='pcraciunoiu', password='testpass')
        user = User.objects.get(username='pcraciunoiu')
        event_cls = (QuestionReplyEvent if event_type == 'reply'
                                        else QuestionSolvedEvent)
        # Make sure 'before' values are the reverse.
        if turn_on:
            assert not event_cls.is_notifying(user, question), (
                '%s should not be notifying.' % event_cls.__name__)
        else:
            assert event_cls.is_notifying(user, question), (
                '%s should be notifying.' % event_cls.__name__)

        url = 'questions.watch' if turn_on else 'questions.unwatch'
        data = {'event_type': event_type} if turn_on else {}
        post(self.client, url, data, args=[question.id])

        if turn_on:
            assert event_cls.is_notifying(user, question), (
                '%s should be notifying.' % event_cls.__name__)
        else:
            assert not event_cls.is_notifying(user, question), (
                '%s should not be notifying.' % event_cls.__name__)
        return question

    @mock.patch_object(Site.objects, 'get_current')
    def test_solution_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        question = self._toggle_watch_question('solution', turn_on=True)
        answer = question.answers.all()[0]
        # Post a reply
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'questions.solution', args=[question.id, answer.id])

        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Solution to: Lorem ipsum dolor sit amet?',
                 body=SOLUTION_EMAIL_INSIDE_REQUEST % answer.id)

        self._toggle_watch_question('solution', turn_on=False)

    @mock.patch_object(Site.objects, 'get_current')
    def test_answer_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        question = self._toggle_watch_question('reply', turn_on=True)
        # Post a reply
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'questions.reply', {'content': 'an answer'},
             args=[question.id])

        answer = Answer.uncached.filter().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='New answer to: Lorem ipsum dolor sit amet?',
                 body=ANSWER_EMAIL_INSIDE_REQUEST % answer.id)

        self._toggle_watch_question('reply', turn_on=False)

    @mock.patch_object(Site.objects, 'get_current')
    def test_solution_notification_deleted(self, get_current):
        """Calling QuestionSolvedEvent.fire() should not query the
        questions_question table.

        This test attempts to simulate the replication lag presumed to cause
        bug 585029.

        """
        get_current.return_value.domain = 'testserver'

        answer = Answer.objects.get(pk=1)
        question = Question.objects.get(pk=1)
        question.solution = answer
        question.save()

        a_user = User.objects.get(username='pcraciunoiu')
        QuestionSolvedEvent.notify(a_user, question)
        event = QuestionSolvedEvent(answer)

        # Delete the question, pretend it hasn't been replicated yet
        Question.objects.get(pk=question.pk).delete()

        event.fire(exclude=question.creator)
        eq_(1, len(mail.outbox))

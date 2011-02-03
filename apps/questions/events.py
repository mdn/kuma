from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from tower import ugettext as _

from notifications.events import InstanceEvent
from questions.models import Question


class QuestionEvent(InstanceEvent):
    """Abstract common functionality between question events."""
    content_type = Question

    def __init__(self, answer):
        super(QuestionEvent, self).__init__(answer.question)
        self.answer = answer


class QuestionReplyEvent(QuestionEvent):
    """An event which fires when a new answer is posted for a question"""
    event_type = 'question reply'

    def _mails(self, users_and_watches):
        # Cache answer.question, similar to caching solution.question below.
        self.answer.question = self.instance
        subject = _('New answer to: %s') % self.instance.title
        t = loader.get_template('questions/email/new_answer.ltxt')
        c = {'answer': self.answer.content,
             'author': self.answer.creator.username,
             'question_title': self.instance.title,
             'host': Site.objects.get_current().domain,
             'answer_url': self.answer.get_absolute_url()}
        content = t.render(Context(c))

        return (EmailMessage(subject, content,
                             settings.NOTIFICATIONS_FROM_ADDRESS,
                             [u.email]) for
                u, dummy in users_and_watches)


class QuestionSolvedEvent(QuestionEvent):
    """An event which fires when a Question gets solved"""
    event_type = 'question solved'

    def _mails(self, users_and_watches):
        question = self.instance
        # Cache solution.question as a workaround for replication lag
        # (bug 585029)
        question.solution = self.answer
        question.solution.question = question

        subject = _('Solution to: %s') % question.title
        t = loader.get_template('questions/email/solution.ltxt')
        c = {'solution': question.solution.content,
             'author': question.creator.username,
             'question_title': question.title,
             'host': Site.objects.get_current().domain,
             'solution_url': question.solution.get_absolute_url()}
        content = t.render(Context(c))
        return (EmailMessage(subject, content,
                             settings.NOTIFICATIONS_FROM_ADDRESS,
                             [u.email]) for
                u, dummy in users_and_watches)

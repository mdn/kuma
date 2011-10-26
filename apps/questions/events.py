from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from tower import ugettext as _

from notifications.events import InstanceEvent
from questions.models import Question
from funfactory.urlresolvers import reverse


class QuestionEvent(InstanceEvent):
    """Abstract common functionality between question events."""
    content_type = Question

    def __init__(self, answer):
        super(QuestionEvent, self).__init__(answer.question)
        self.answer = answer

    @classmethod
    def _activation_email(cls, watch, email):
        """Return an EmailMessage containing the activation URL to be sent to
        a new watcher."""
        subject = _('Please confirm your email address')
        email_kwargs = {'activation_url': cls._activation_url(watch),
                        'domain': Site.objects.get_current().domain,
                        'watch_description': cls.get_watch_description(watch)}
        template_path = 'questions/email/activate_watch.ltxt'
        message = loader.render_to_string(template_path, email_kwargs)
        return EmailMessage(subject, message,
                            settings.NOTIFICATIONS_FROM_ADDRESS, [email])

    @classmethod
    def _activation_url(cls, watch):
        return reverse('questions.activate_watch',
                       args=[watch.id, watch.secret])


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

    @classmethod
    def get_watch_description(cls, watch):
        return _('New answers for question: %s') % watch.content_object.title


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

    @classmethod
    def get_watch_description(cls, watch):
        question = watch.content_object
        return _('Solution found for question: %s') % question.title

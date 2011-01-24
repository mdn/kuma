from notifications.events import Event
from questions.models import Question


class QuestionSolvedEvent(Event):
    """A event which fires when a Question gets solved"""

    event_type = 'question solved'
    content_type = Question
    filters = set('id')

    def __init__(self, question):
        self.instance = question

    @classmethod
    def notify(cls, question, user_or_email):
        """Create, save, and return a Watch which fires when `question` is
        solved."""
        return super(QuestionSolvedEvent, cls).notify(user_or_email,
                                                      id=question.pk)

    def _users_watching(self):
        return self._users_watching_by_filter(id=self.instance.pk)

    def _mails(self, users):
        # TODO: Implement. This does any necessary templating.
        # Let's not concretize possibly thousands of mails in memory.
        pass

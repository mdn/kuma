from notifications.events import Event
from questions.models import Question


class QuestionSolvedEvent(Event):
    """A event which fires when a Question gets solved"""

    event_type = 'question solved'
    content_type = Question
    filters = {'id': 'id  '}

    def __init__(self, question):
        self.instance = question

    @classmethod
    def watch(cls, question, user):  # Should this take user? Email? Both?
        """Create, save, and return a Watch which fires when `question` is
        solved."""
        # TODO: Implement. This will probably spawn a helper function to live
        # in Event or at the module level of notifications.events.

    def _watches(self):
        return self._watches_core(id=self.instance.pk)

    def _build_mails(self, users):
        # TODO: Implement. This does any necessary templating.
        # Let's not concretize possibly thousands of mails in memory.
        pass

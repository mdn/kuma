from notifications.events import InstanceEvent
from questions.models import Question


class QuestionSolvedEvent(InstanceEvent):
    """A event which fires when a Question gets solved"""

    event_type = 'question solved'
    content_type = Question

    def _mails(self, users):
        # TODO: Implement. This does any necessary templating.
        # Let's not concretize possibly thousands of mails in memory.
        pass

from celery.messaging import establish_connection
import cronjobs

from questions.models import Question
from questions.tasks import update_question_vote_chunk
from sumo.utils import chunked


@cronjobs.register
def update_weekly_votes():
    """Keep the num_votes_past_week value accurate."""

    questions = Question.objects.all().values_list('pk', flat=True)

    with establish_connection() as conn:
        for chunk in chunked(questions, 200):
            update_question_vote_chunk.apply_async(args=[chunk],
                                                   connection=conn)

import cronjobs

from .models import Question


@cronjobs.register
def update_weekly_votes():
    """Keep the num_votes_past_week value accurate."""

    questions = Question.objects.all()

    for q in questions:
        q.sync_num_votes_past_week()
        q.save(no_update=True)

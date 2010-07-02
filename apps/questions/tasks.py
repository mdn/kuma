import logging

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User

from celery.decorators import task


log = logging.getLogger('k.task')


@task(rate_limit='1/s')
def update_question_votes(q):
    log.debug('Got a new QuestionVote.')
    q.sync_num_votes_past_week()
    q.save(no_update=True)


@task
def cache_top_contributors():
    """Compute the top contributors and store in cache."""
    log.info('Computing the top contributors.')
    sql = '''SELECT u.*, COUNT(*) AS num_solutions
             FROM auth_user AS u, questions_answer AS a,
                  questions_question AS q
             WHERE u.id = a.creator_id AND a.id = q.solution_id AND
                   a.created >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
             GROUP BY u.id
             ORDER BY num_solutions DESC
             LIMIT 10'''
    users = list(User.objects.raw(sql))
    cache.set(settings.TOP_CONTRIBUTORS_CACHE_KEY, users,
              settings.TOP_CONTRIBUTORS_CACHE_TIMEOUT)

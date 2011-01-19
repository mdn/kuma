import logging

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import transaction
from django.template import Context, loader

from celery.decorators import task
from tower import ugettext as _

from notifications.tasks import send_notification
from questions import ANSWERS_PER_PAGE


log = logging.getLogger('k.task')


@task(rate_limit='1/s')
def update_question_votes(q):
    log.debug('Got a new QuestionVote.')
    q.sync_num_votes_past_week()
    q.save(no_update=True, force_update=True)


@task(rate_limit='15/m')
def update_question_vote_chunk(data, **kwargs):
    """Update num_votes_past_week for a number of questions."""
    log.info('Calculating past week votes for %s questions.' % len(data))

    # Import here to avoid a circle.
    from questions.models import Question

    for pk in data:
        try:
            question = Question.objects.get(pk=pk)
            question.sync_num_votes_past_week()
            question.save(no_update=True)
        except Question.DoesNotExist:
            log.debug('Missing question: %d' % pk)
    transaction.commit_unless_managed()


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


@task
def build_answer_notification(answer):
    ct = ContentType.objects.get_for_model(answer.question)

    subject = _('New answer to: %s') % answer.question.title
    t = loader.get_template('questions/email/new_answer.ltxt')
    c = {'answer': answer.content, 'author': answer.creator.username,
         'question_title': answer.question.title,
         'host': Site.objects.get_current().domain,
         'answer_url': answer.get_absolute_url()}
    content = t.render(Context(c))
    exclude = (answer.creator.email,)

    send_notification.delay(ct, answer.question.pk, subject,
                            content, exclude, 'reply')


@task
def build_solution_notification(question):
    """Send emails to everyone watching the question--except the asker."""
    ct = ContentType.objects.get_for_model(question)
    # Cache solution.question as a workaround for replication lag (bug 585029)
    question.solution.question = question

    subject = _('Solution to: %s') % question.title
    t = loader.get_template('questions/email/solution.ltxt')
    c = {'solution': question.solution.content,
         'author': question.creator.username,
         'question_title': question.title,
         'host': Site.objects.get_current().domain,
         'solution_url': question.solution.get_absolute_url()}
    content = t.render(Context(c))
    exclude = (question.creator.email,)

    send_notification.delay(ct, question.pk, subject, content,
                            exclude, 'solution')


@task(rate_limit='4/m')
def update_answer_pages(question):
    log.debug('Recalculating answer page numbers for question %s: %s' %
              (question.pk, question.title))

    i = 0
    for answer in question.answers.using('default').order_by('created').all():
        answer.page = i / ANSWERS_PER_PAGE + 1
        answer.save(no_update=True, no_notify=True)
        i += 1

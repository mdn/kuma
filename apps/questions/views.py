from django.shortcuts import get_object_or_404

import jingo

from sumo.utils import paginate
from .models import QuestionForum, Question


def question_forums(request):
    """View all question forums."""

    forums = QuestionForum.objects.all()

    return jingo.render(request, 'questions/forums.html',
                        {'forums': forums})


def questions(request, forum_slug):
    """View all the questions in a question forum."""

    forum = get_object_or_404(QuestionForum, slug=forum_slug)

    questions_ = paginate(forum.question_set.all())

    return jingo.render(request, 'questions/questions.html',
                        {'forum': forum, 'questions': questions_})


def answers(request, forum_slug, question_id):
    """View the answers to a question."""

    forum = get_object_or_404(QuestionForum, slug=forum_slug)
    question = get_object_or_404(Question, pk=question_id)

    answers_ = paginate(question.answer_set.all())

    return jingo.render(request, 'questions/answers.html',
                        {'forum': forum, 'question': question,
                         'answers': answers_})


def new_question(request, forum_slug):
    """Ask a new question."""
    pass


def reply(request, forum_slug, question_id):
    """Post a new answer to a question."""
    pass

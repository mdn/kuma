from django.shortcuts import get_object_or_404

import jingo

from sumo.utils import paginate
from .models import Question
import questions as constants


def questions(request):
    """View the questions."""

    questions_ = paginate(request, Question.objects.all(),
                          per_page=constants.QUESTIONS_PER_PAGE)

    return jingo.render(request, 'questions/questions.html',
                        {'questions': questions_})


def answers(request, question_id):
    """View the answers to a question."""

    question = get_object_or_404(Question, pk=question_id)

    answers_ = paginate(request, question.answers.all(),
                        per_page=constants.ANSWERS_PER_PAGE)

    return jingo.render(request, 'questions/answers.html',
                        {'question': question, 'answers': answers_})


def new_question(request):
    """Ask a new question."""
    pass


def reply(request, question_id):
    """Post a new answer to a question."""
    pass

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

import jingo

from sumo.utils import paginate
from sumo.urlresolvers import reverse
from .models import Question, Answer
from .forms import NewQuestionForm, AnswerForm
from .feeds import QuestionsFeed, AnswersFeed
import questions as constants
import question_config as config


def questions(request):
    """View the questions."""

    questions_ = paginate(request, Question.objects.all(),
                          per_page=constants.QUESTIONS_PER_PAGE)

    feed_urls = ((reverse('questions.feed'),
                  QuestionsFeed().title()),)

    return jingo.render(request, 'questions/questions.html',
                        {'questions': questions_,
                         'feeds': feed_urls})


def answers(request, question_id, form=None):
    """View the answers to a question."""

    question = get_object_or_404(Question, pk=question_id)
    answers_ = paginate(request, question.answers.all(),
                        per_page=constants.ANSWERS_PER_PAGE)

    if not form:
        form = AnswerForm()

    feed_urls = ((reverse('questions.answers.feed',
                          kwargs={'question_id': question_id}),
                  AnswersFeed().title(question)),)

    return jingo.render(request, 'questions/answers.html',
                        {'question': question, 'answers': answers_,
                         'form': form, 'feeds': feed_urls})


def new_question(request):
    """Ask a new question."""

    product = _get_current_product(request)
    category = _get_current_category(request)
    articles = _get_articles(category)

    if request.method == 'GET':
        search = request.GET.get('search', None)
        search_results = None
        if search:
            search_results = True  # TODO - get the search results

        form = None
        if request.GET.get('showform', False):
            form = NewQuestionForm(user=request.user, product=product,
                                   category=category,
                                   initial={'title': search})

        return jingo.render(request, 'questions/new_question.html',
                            {'form': form, 'search_results': search_results,
                             'products': config.products,
                             'current_product': product,
                             'current_category': category,
                             'current_articles': articles})

    # Handle the form post
    form = NewQuestionForm(user=request.user, product=product,
                           category=category, data=request.POST)

    if form.is_valid():
        question = Question(creator=request.user,
                            title=form.cleaned_data['title'],
                            content=form.cleaned_data['content'])
        question.save()
        question.add_metadata(**form.cleaned_metadata)
        if product:
            question.add_metadata(product=product['name'])
        if category:
            question.add_metadata(category=category['name'])

        return HttpResponseRedirect(
            reverse('questions.answers', args=[question.id]))

    return jingo.render(request, 'questions/new_question.html',
                        {'form': form, 'products': config.products,
                         'current_product': product,
                         'current_category': category,
                         'current_articles': articles})


@require_POST
@login_required
def reply(request, question_id):
    """Post a new answer to a question."""
    form = AnswerForm(request.POST)
    if form.is_valid():
        question = get_object_or_404(Question, pk=question_id)
        answer = Answer(question=question, creator=request.user,
                        content=form.cleaned_data['content'])
        answer.save()

        return HttpResponseRedirect(answer.get_absolute_url())

    return answers(request, question_id, form)


@require_POST
@login_required
def solution(request, question_id, answer_id):
    """Accept an answer as the solution to the question."""
    question = get_object_or_404(Question, pk=question_id)
    answer = get_object_or_404(Answer, pk=answer_id)

    if question.creator != request.user:
        return HttpResponseForbidden()

    question.solution = answer
    question.save()

    return HttpResponseRedirect(answer.get_absolute_url())


#  Helper functions to deal with products dict
def _get_current_product(request):
    """Get the selected product."""
    product_key = request.GET.get('product', None)
    if product_key:
        filtered = filter(lambda x: x['key'] == product_key, config.products)
        if len(filtered) > 0:
            return filtered[0]
    return None


def _get_current_category(request):
    """Get the selected category."""
    product = _get_current_product(request)
    category_key = request.GET.get('category', None)
    if category_key and product:
        categories = product['categories']
        filtered = filter(lambda x: x['key'] == category_key, categories)
        if len(filtered) > 0:
            return filtered[0]
    return None


def _get_articles(category):
    """Get the articles for the specified category."""
    if category:
        return category['articles']
    return None

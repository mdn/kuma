from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q

import jingo

from sumo.utils import paginate
from sumo.urlresolvers import reverse
from .models import Question, Answer, QuestionVote, AnswerVote
from .forms import NewQuestionForm, AnswerForm
from .feeds import QuestionsFeed, AnswersFeed
import questions as constants
import question_config as config


def questions(request):
    """View the questions."""

    filter = request.GET.get('filter')

    if filter == 'no-replies':
        question_qs = Question.objects.filter(num_answers=0)
    elif filter == 'replies':
        question_qs = Question.objects.filter(num_answers__gt=0)
    elif filter == 'solved':
        question_qs = Question.objects.exclude(solution=None)
    elif filter == 'unsolved':
        question_qs = Question.objects.filter(solution=None)
    elif filter == 'my-contributions' and request.user.is_authenticated():
        criteria = Q(answers__creator=request.user) | Q(creator=request.user)
        question_qs = Question.objects.filter(criteria).distinct()
    else:
        question_qs = Question.objects.all()
        filter = None

    questions_ = paginate(request, question_qs,
                          per_page=constants.QUESTIONS_PER_PAGE)

    feed_urls = ((reverse('questions.feed'),
                  QuestionsFeed().title()),)

    return jingo.render(request, 'questions/questions.html',
                        {'questions': questions_,
                         'feeds': feed_urls, 'filter': filter})


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

        # Submitting the question counts as a vote
        return question_vote(request, question.id)

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


@require_POST
def question_vote(request, question_id):
    """I have this problem too."""
    question = get_object_or_404(Question, pk=question_id)

    if not question.has_voted(request):
        vote = QuestionVote(question=question)

        if request.user.is_authenticated():
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        vote.save()

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
def answer_vote(request, question_id, answer_id):
    """Vote for Helpful/Not Helpful answers"""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)

    if not answer.has_voted(request):
        vote = AnswerVote(answer=answer)

        if 'helpful' in request.POST:
            vote.helpful = True

        if request.user.is_authenticated():
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        vote.save()

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

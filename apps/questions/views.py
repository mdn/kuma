import json
import logging

from django.contrib.auth.decorators import permission_required
from django.http import (HttpResponseRedirect, HttpResponse,
                         HttpResponseBadRequest, HttpResponseForbidden)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import PermissionDenied

import jingo
from taggit.models import Tag
from tower import ugettext_lazy as _lazy

from sumo.utils import paginate
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from access.decorators import has_perm_or_owns_or_403
from .models import Question, Answer, QuestionVote, AnswerVote
from .forms import NewQuestionForm, AnswerForm
from .feeds import QuestionsFeed, AnswersFeed
from .tags import add_existing_tag
from .tasks import cache_top_contributors
import questions as constants
import question_config as config


log = logging.getLogger('k.questions')


UNAPPROVED_TAG = _lazy(u'That tag does not exist.')
NO_TAG = _lazy(u'Please provide a tag.')


def questions(request):
    """View the questions."""

    filter = request.GET.get('filter')
    tagged = request.GET.get('tagged')
    tags = None
    sort_ = request.GET.get('sort')

    if sort_ == 'requested':
        order = '-num_votes_past_week'
    else:
        sort_ = None
        order = '-updated'

    if filter == 'no-replies':
        question_qs = Question.objects.filter(num_answers=0).order_by(order)
    elif filter == 'replies':
        question_qs = Question.objects.filter(num_answers__gt=0)
        question_qs = question_qs.order_by(order)
    elif filter == 'solved':
        question_qs = Question.objects.exclude(solution=None).order_by(order)
    elif filter == 'unsolved':
        question_qs = Question.objects.filter(solution=None).order_by(order)
    elif filter == 'my-contributions' and request.user.is_authenticated():
        criteria = Q(answers__creator=request.user) | Q(creator=request.user)
        question_qs = Question.objects.filter(criteria).distinct()
        question_qs = question_qs.order_by(order)
    else:
        question_qs = Question.objects.all().order_by(order)
        filter = None

    if tagged:
        tag_slugs = tagged.split(',')
        tags = Tag.objects.filter(slug__in=tag_slugs)
        if tags:
            question_qs = question_qs.filter(tags__in=[t.name for t in tags])
        else:
            question_qs = Question.objects.get_empty_query_set()

    questions_ = paginate(request, question_qs,
                          per_page=constants.QUESTIONS_PER_PAGE)

    feed_urls = ((reverse('questions.feed'),
                  QuestionsFeed().title()),)

    return jingo.render(request, 'questions/questions.html',
                        {'questions': questions_, 'feeds': feed_urls,
                         'filter': filter, 'sort': sort_,
                         'top_contributors': _get_top_contributors(),
                         'tags': tags, 'tagged': tagged})


def answers(request, question_id, form=None):
    """View the answers to a question."""
    return jingo.render(request, 'questions/answers.html',
                        _answers_data(request, question_id, form))


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
    question = get_object_or_404(Question, pk=question_id)
    if question.is_locked:
        raise PermissionDenied

    form = AnswerForm(request.POST)
    if form.is_valid():
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
    if question.is_locked:
        raise PermissionDenied

    if question.creator != request.user:
        return HttpResponseForbidden()

    question.solution = answer
    question.save()

    return HttpResponseRedirect(answer.get_absolute_url())


@require_POST
def question_vote(request, question_id):
    """I have this problem too."""
    question = get_object_or_404(Question, pk=question_id)
    if question.is_locked:
        raise PermissionDenied

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
    if answer.question.is_locked:
        raise PermissionDenied

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


@permission_required('questions.tag_question')
def add_tag(request, question_id):
    """Add a (case-insensitive) tag to question.

    If the question already has the tag, do nothing.

    """
    # If somebody hits Return in the address bar after provoking an error from
    # the add form, nicely send them back to the question:
    if request.method == 'GET':
        return HttpResponseRedirect(
            reverse('questions.answers', args=[question_id]))

    try:
        canonical_name = _add_tag(request, question_id)
    except Tag.DoesNotExist:
        template_data = _answers_data(request, question_id)
        template_data['tag_adding_error'] = UNAPPROVED_TAG
        template_data['tag_adding_value'] = request.POST.get('tag-name', '')
        return jingo.render(request, 'questions/answers.html', template_data)

    if canonical_name:  # success
        return HttpResponseRedirect(
            reverse('questions.answers', args=[question_id]))

    # No tag provided
    template_data = _answers_data(request, question_id)
    template_data['tag_adding_error'] = NO_TAG
    return jingo.render(request, 'questions/answers.html', template_data)


@permission_required('questions.tag_question')
@require_POST
def add_tag_async(request, question_id):
    """Add a (case-insensitive) tag to question asyncronously. Return empty.

    If the question already has the tag, do nothing.

    """
    try:
        canonical_name = _add_tag(request, question_id)
    except Tag.DoesNotExist:
        return HttpResponse(json.dumps({'error': unicode(UNAPPROVED_TAG)}),
                            mimetype='application/x-json',
                            status=400)

    if canonical_name:
        tag = Tag.objects.get(name=canonical_name)
        tag_url = urlparams(reverse('questions.questions'), tagged=tag.slug)
        data = {'canonicalName': canonical_name,
                'tagUrl': tag_url}
        return HttpResponse(json.dumps(data),
                            mimetype='application/x-json')

    return HttpResponse(json.dumps({'error': unicode(NO_TAG)}),
                        mimetype='application/x-json',
                        status=400)


@permission_required('questions.tag_question')
@require_POST
def remove_tag(request, question_id):
    """Remove a (case-insensitive) tag from question.

    Expects a POST with the tag name embedded in a field name, like
    remove-tag-tagNameHere. If question doesn't have that tag, do nothing.

    """
    prefix = 'remove-tag-'
    names = [k for k in request.POST if k.startswith(prefix)]
    if names:
        name = names[0][len(prefix):]
        question = get_object_or_404(Question, pk=question_id)
        question.tags.remove(name)

    return HttpResponseRedirect(
        reverse('questions.answers', args=[question_id]))


@permission_required('questions.tag_question')
@require_POST
def remove_tag_async(request, question_id):
    """Remove a (case-insensitive) tag from question.

    If question doesn't have that tag, do nothing. Return value is JSON.

    """
    name = request.POST.get('name')
    if name:
        question = get_object_or_404(Question, pk=question_id)
        question.tags.remove(name)
        return HttpResponse('{}', mimetype='application/x-json')

    return HttpResponseBadRequest(json.dumps({'error': unicode(NO_TAG)}),
                                  mimetype='application/x-json')


@login_required
@permission_required('questions.delete_question')
def delete_question(request, question_id):
    """Delete a question"""
    question = get_object_or_404(Question, pk=question_id)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'questions/confirm_question_delete.html',
                            {'question': question})

    # Handle confirm delete form POST
    log.warning('User %s is deleting question with id=%s' %
                (request.user, question.id))
    question.delete()

    return HttpResponseRedirect(reverse('questions.questions'))


@login_required
@permission_required('questions.delete_answer')
def delete_answer(request, question_id, answer_id):
    """Delete an answer"""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'questions/confirm_answer_delete.html',
                            {'answer': answer})

    # Handle confirm delete form POST
    log.warning('User %s is deleting answer with id=%s' %
                (request.user, answer.id))
    answer.delete()

    return HttpResponseRedirect(reverse('questions.answers',
                                args=[question_id]))


@require_POST
@login_required
@permission_required('questions.lock_question')
def lock_question(request, question_id):
    """Lock a question"""
    question = get_object_or_404(Question, pk=question_id)
    question.is_locked = not question.is_locked
    log.info("User %s set is_locked=%s on question with id=%s " %
             (request.user, question.is_locked, question.id))
    question.save()

    return HttpResponseRedirect(question.get_absolute_url())

@login_required
@has_perm_or_owns_or_403('questions.change_answer', 'creator',
                         (Answer, 'id__iexact', 'answer_id'),
                         (Answer, 'id__iexact', 'answer_id'))
def edit_answer(request, question_id, answer_id):
    """Edit an answer."""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)

    if answer.question.is_locked:
        raise PermissionDenied

    if request.method == 'GET':
        form = AnswerForm({'content': answer.content})
        return jingo.render(request, 'questions/edit_answer.html',
                            {'form': form, 'answer': answer})

    form = AnswerForm(request.POST)

    if form.is_valid():
        log.warning('User %s is editing answer with id=%s' %
                    (request.user, answer.id))
        answer.content = form.cleaned_data['content']
        answer.updated_by = request.user
        answer.save()

        return HttpResponseRedirect(answer.get_absolute_url())

    return jingo.render(request, 'questions/edit_answer.html',
                        {'form': form, 'answer': answer})


def _answers_data(request, question_id, form=None):
    """Return a map of the minimal info necessary to draw an answers page."""
    question = get_object_or_404(Question, pk=question_id)
    answers_ = paginate(request, question.answers.all(),
                        per_page=constants.ANSWERS_PER_PAGE)
    vocab = [t.name for t in Tag.objects.all()]  # TODO: Fetch only name.
    feed_urls = ((reverse('questions.answers.feed',
                          kwargs={'question_id': question_id}),
                  AnswersFeed().title(question)),)
    related = question.tags.similar_objects()[:3]

    return {'question': question,
            'answers': answers_,
            'related': related,
            'form': form or AnswerForm(),
            'feeds': feed_urls,
            'tag_vocab': json.dumps(vocab),
            'can_tag': request.user.has_perm('questions.tag_question'),
            'can_create_tags': request.user.has_perm('taggit.add_tag')}


def _add_tag(request, question_id):
    """Add a named tag to a question, creating it first if appropriate.

    Tag name (case-insensitive) must be in request.POST['tag-name'].

    If there is no such tag and the user is not allowed to make new tags, raise
    Tag.DoesNotExist. If no tag name is provided, return None. Otherwise,
    return the canonicalized tag name.

    """
    tag_name = request.POST.get('tag-name', '').strip()
    if tag_name:
        question = get_object_or_404(Question, pk=question_id)
        try:
            canonical_name = add_existing_tag(tag_name, question.tags)
        except Tag.DoesNotExist:
            if request.user.has_perm('taggit.add_tag'):
                question.tags.add(tag_name)  # implicitly creates if needed
                return tag_name
            raise
        return canonical_name


def _get_top_contributors():
    """Retrieves the top contributors from cache, if available.
    Otherwise it creates a task for computing and caching them.

    These are the users with the most solutions in the last week.
    """
    users = cache.get(settings.TOP_CONTRIBUTORS_CACHE_KEY)
    if not users:
        cache_top_contributors.delay()
    return users


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

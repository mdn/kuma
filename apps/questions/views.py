from itertools import islice
import json
import logging
from datetime import datetime

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                         HttpResponseBadRequest, HttpResponseForbidden)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings
from django.contrib.sites.models import Site

import jingo
from taggit.models import Tag
from tower import ugettext as _
from tower import ugettext_lazy as _lazy

from access.decorators import has_perm_or_owns_or_403
from search.clients import WikiClient, QuestionsClient, SearchError
from search.utils import locale_or_default, sphinx_locale
from sumo.models import WikiPage
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from sumo.utils import paginate
from notifications import create_watch, destroy_watch
from .models import (Question, Answer, QuestionVote, AnswerVote,
                     CONFIRMED, UNCONFIRMED)
from .forms import (NewQuestionForm, EditQuestionForm,
                    AnswerForm, WatchQuestionForm,
                    FREQUENCY_CHOICES)
from .feeds import QuestionsFeed, AnswersFeed, TaggedQuestionsFeed
from .tags import add_existing_tag
from .tasks import (cache_top_contributors, build_solution_notification,
                    send_confirmation_email)
import questions as constants
from .question_config import products
from upload.models import ImageAttachment
from upload.views import upload_images


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

    question_qs = Question.objects.filter(status=CONFIRMED)
    if filter == 'no-replies':
        question_qs = question_qs.filter(num_answers=0)
    elif filter == 'replies':
        question_qs = question_qs.filter(num_answers__gt=0)
    elif filter == 'solved':
        question_qs = question_qs.exclude(solution=None)
    elif filter == 'unsolved':
        question_qs = question_qs.filter(solution=None)
    elif filter == 'my-contributions' and request.user.is_authenticated():
        criteria = Q(answers__creator=request.user) | Q(creator=request.user)
        question_qs = question_qs.filter(criteria).distinct()
    else:
        filter = None

    feed_urls = ((reverse('questions.feed'),
                  QuestionsFeed().title()),)

    if tagged:
        tag_slugs = tagged.split(',')
        tags = Tag.objects.filter(slug__in=tag_slugs)
        if tags:
            for t in tags:
                question_qs = question_qs.filter(tags__in=[t.name])
            if len(tags) == 1:
                feed_urls += ((reverse('questions.tagged_feed',
                                       args=[tags[0].slug]),
                               TaggedQuestionsFeed().title(tags[0])),)
        else:
            question_qs = Question.objects.get_empty_query_set()

    question_qs = question_qs.order_by(order)
    questions_ = paginate(request, question_qs,
                          per_page=constants.QUESTIONS_PER_PAGE)

    return jingo.render(request, 'questions/questions.html',
                        {'questions': questions_, 'feeds': feed_urls,
                         'filter': filter, 'sort': sort_,
                         'top_contributors': _get_top_contributors(),
                         'tags': tags, 'tagged': tagged})


def answers(request, question_id, form=None, watch_form=None,
            answer_preview=None):
    """View the answers to a question."""
    ans_ = _answers_data(request, question_id, form, watch_form,
                         answer_preview)
    if request.user.is_authenticated():
        ans_['images'] = ans_['question'].images.filter(creator=request.user)
    return jingo.render(request, 'questions/answers.html', ans_)


def new_question(request):
    """Ask a new question."""

    product_key = request.GET.get('product')
    product = products.get(product_key)
    if product_key and not product:
        raise Http404
    category_key = request.GET.get('category')
    if product and category_key:
        category = product['categories'].get(category_key)
        if not category:
            raise Http404
        deadend = category.get('deadend', False)
        html = category.get('html')
        articles = category.get('articles')
    else:
        category = None
        deadend = product.get('deadend', False) if product else False
        html = product.get('html') if product else None
        articles = None

    if request.method == 'GET':
        search = request.GET.get('search', '')
        if search:
            try:
                search_results = _search_suggestions(
                                 search, locale_or_default(request.locale))
            except SearchError:
                # Just quietly advance the user to the next step.
                search_results = []
            tried_search = True
        else:
            search_results = []
            tried_search = False

        if request.GET.get('showform'):
            # Before we show the form, make sure the user is auth'd:
            if not request.user.is_authenticated():
                return HttpResponseRedirect(settings.LOGIN_URL)
            form = NewQuestionForm(product=product,
                                   category=category,
                                   initial={'title': search})
        else:
            form = None

        return jingo.render(request, 'questions/new_question.html',
                            {'form': form, 'search_results': search_results,
                             'tried_search': tried_search,
                             'products': products,
                             'current_product': product,
                             'current_category': category,
                             'current_html': html,
                             'current_articles': articles,
                             'deadend': deadend,
                             'host': Site.objects.get_current().domain})

    # Handle the form post
    if not request.user.is_authenticated():
        return HttpResponseRedirect(settings.LOGIN_URL)
    form = NewQuestionForm(product=product, category=category,
                           data=request.POST)

    if form.is_valid():
        question = Question(creator=request.user,
                            title=form.cleaned_data['title'],
                            content=form.cleaned_data['content'])
        question.save()
        question.add_metadata(**form.cleaned_metadata)
        if product:
            question.add_metadata(product=product['key'])
            if category:
                question.add_metadata(category=category['key'])

        # The first time a question is saved, automatically apply some tags:
        question.auto_tag()

        # Submitting the question counts as a vote
        question_vote(request, question.id)

        send_confirmation_email.delay(question)
        return jingo.render(request, 'questions/confirm_question.html',
                            {'question': question})

    return jingo.render(request, 'questions/new_question.html',
                        {'form': form, 'products': products,
                         'current_product': product,
                         'current_category': category,
                         'current_articles': articles})


@require_http_methods(['GET', 'POST'])
@login_required
@has_perm_or_owns_or_403('questions.change_question', 'creator',
                         (Question, 'id__exact', 'question_id'),
                         (Question, 'id__exact', 'question_id'))
def edit_question(request, question_id):
    """Edit a question."""
    question = get_object_or_404(Question, pk=question_id)
    user = request.user

    if not user.has_perm('questions.change_question') and question.is_locked:
        raise PermissionDenied

    if request.method == 'GET':
        initial = question.metadata.copy()
        initial.update(title=question.title, content=question.content)
        form = EditQuestionForm(product=question.product,
                                category=question.category,
                                initial=initial)
    else:
        form = EditQuestionForm(data=request.POST,
                                product=question.product,
                                category=question.category)
        if form.is_valid():
            question.title = form.cleaned_data['title']
            question.content = form.cleaned_data['content']
            question.updated_by = user
            question.save()

            # TODO: Factor all this stuff up from here and new_question into
            # the form, which should probably become a ModelForm.
            question.clear_mutable_metadata()
            question.add_metadata(**form.cleaned_metadata)

            return HttpResponseRedirect(reverse('questions.answers',
                                        kwargs={'question_id': question.id}))

    return jingo.render(request, 'questions/edit_question.html',
                        {'question': question,
                         'form': form,
                         'current_product': question.product,
                         'current_category': question.category})


def confirm_question_form(request, question_id, confirmation_id):
    """Confirm a question submitted."""
    question = get_object_or_404(Question, pk=question_id,
                                 confirmation_id=confirmation_id)

    if question.status == UNCONFIRMED:
        if request.method == 'GET':
            template = 'questions/confirm_question_form.html'
            return jingo.render(request, template,
                                {'question': question})
        else:
            log.info("User %s is confirming question with id=%s " %
                     (question.creator, question.id))
            question.status = CONFIRMED
            question.save()

    return HttpResponseRedirect(reverse('questions.answers',
                                        args=[question_id]))


@require_POST
@login_required
def reply(request, question_id):
    """Post a new answer to a question."""
    question = get_object_or_404(Question, pk=question_id)
    answer_preview = None
    if question.is_locked:
        raise PermissionDenied

    form = AnswerForm(request.POST)

    # NOJS: delete images
    if 'delete_images' in request.POST:
        for image_id in request.POST.getlist('delete_image'):
            ImageAttachment.objects.get(pk=image_id).delete()

        return answers(request, question_id, form)

    # NOJS: upload image
    if 'upload_image' in request.POST:
        upload_images(request, question)
        return answers(request, question_id, form)

    if form.is_valid():
        answer = Answer(question=question, creator=request.user,
                        content=form.cleaned_data['content'])
        if 'preview' in request.POST:
            answer_preview = answer
        else:
            answer.save()
            ct = ContentType.objects.get_for_model(answer)
            # Move over to the answer all of the images I added to the
            # reply form
            up_images = question.images.filter(creator=request.user)
            up_images.update(content_type=ct, object_id=answer.id)

            return HttpResponseRedirect(answer.get_absolute_url())

    return answers(request, question_id, form, answer_preview=answer_preview)


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
    build_solution_notification.delay(question)

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

        if request.is_ajax():
            tmpl = 'questions/includes/question_vote_thanks.html'
            form = _init_watch_form(request)
            html = jingo.render_to_string(request, tmpl, {'question': question,
                                                          'watch_form': form})
            return HttpResponse(json.dumps({'html': html}))

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
    answer_preview = None
    if answer.question.is_locked:
        raise PermissionDenied

    # NOJS: upload images, if any
    upload_images(request, answer)

    if request.method == 'GET':
        form = AnswerForm({'content': answer.content})
        return jingo.render(request, 'questions/edit_answer.html',
                            {'form': form, 'answer': answer})

    form = AnswerForm(request.POST)

    if form.is_valid():
        answer.content = form.cleaned_data['content']
        answer.updated_by = request.user
        if 'preview' in request.POST:
            answer.updated = datetime.now()
            answer_preview = answer
        else:
            log.warning('User %s is editing answer with id=%s' %
                        (request.user, answer.id))
            answer.save()
            return HttpResponseRedirect(answer.get_absolute_url())

    return jingo.render(request, 'questions/edit_answer.html',
                        {'form': form, 'answer': answer,
                         'answer_preview': answer_preview})


@require_POST
def watch_question(request, question_id):
    """Start watching a question for replies or solution."""
    question = get_object_or_404(Question, pk=question_id)
    form = WatchQuestionForm(request.POST)

    # Process the form
    if form.is_valid():
        if request.user.is_authenticated():
            email = request.user.email
        else:
            email = form.cleaned_data['email']
        event_type = form.cleaned_data['event_type']
        create_watch(Question, question.id, email, event_type)

    # Respond to ajax request
    if request.is_ajax():
        if form.is_valid():
            msg = _('You will be notified of updates by email.')
            return HttpResponse(json.dumps({'message': msg}))

        if request.POST.get('from_vote'):
            tmpl = 'questions/includes/question_vote_thanks.html'
        else:
            tmpl = 'questions/includes/email_subscribe.html'

        html = jingo.render_to_string(request, tmpl, {'question': question,
                                                      'watch_form': form})
        return HttpResponse(json.dumps({'html': html}))

    # Respond to normal request
    if form.is_valid():
        return HttpResponseRedirect(question.get_absolute_url())

    return answers(request, question.id, watch_form=form)


@require_POST
@login_required
def unwatch_question(request, question_id):
    """Stop watching a question."""
    question = get_object_or_404(Question, pk=question_id)
    destroy_watch(Question, question.id, request.user.email)
    return HttpResponseRedirect(question.get_absolute_url())


def _search_suggestions(query, locale):
    """Return an iterable of the most relevant wiki pages and questions.

    query -- full text to search on
    locale -- locale to limit to

    Items returned are dicts:
        { 'url': URL where the article can be viewed,
          'title': Title of the article,
          'excerpt_html': Excerpt of the article with search terms hilighted,
                          formatted in HTML }

    Weights wiki pages infinitely higher than questions at the moment.

    """
    def prepare(result, model, searcher, result_to_id):
        """Turn a search result from a Sphinx client into a dict for templates.

        Return {} if an object corresponding to the result cannot be found.

        """
        try:
            obj = model.objects.get(pk=result_to_id(result))
        except ObjectDoesNotExist:
            return {}
        return {'url': obj.get_absolute_url(),
                'title': obj.title,
                'excerpt_html': searcher.excerpt(obj.content, query)}

    max_suggestions = settings.QUESTIONS_MAX_SUGGESTIONS
    query_limit = max_suggestions + settings.QUESTIONS_SUGGESTION_SLOP

    # Search wiki pages:
    wiki_searcher = WikiClient()
    filters = [{'filter': 'locale',
                'value': (sphinx_locale(locale),)},
               {'filter': 'category',
                'value': [x for x in settings.SEARCH_DEFAULT_CATEGORIES
                          if x >= 0]},
               {'filter': 'category',
                'exclude': True,
                'value': [-x for x in settings.SEARCH_DEFAULT_CATEGORIES
                          if x < 0]}]
    raw_results = wiki_searcher.query(query, filters=filters,
                                      limit=query_limit)
    # Lazily build excerpts from results. Stop when we have enough:
    results = islice((p for p in
                       (prepare(r, WikiPage, wiki_searcher, lambda x: x['id'])
                        for r in raw_results) if p),
                     max_suggestions)
    results = list(results)

    # If we didn't find enough wiki pages to fill the page, pad it out with
    # other questions:
    if len(results) < max_suggestions:
        question_searcher = QuestionsClient()
        # questions app is en-US only.
        raw_results = question_searcher.query(query,
                                              limit=query_limit - len(results))
        results.extend(islice((p for p in
                               (prepare(r, Question, question_searcher,
                                        lambda x: x['attrs']['question_id'])
                                for r in raw_results) if p),
                              max_suggestions - len(results)))

    return results


def _answers_data(request, question_id, form=None, watch_form=None,
                  answer_preview=None):
    """Return a map of the minimal info necessary to draw an answers page."""
    question = get_object_or_404(Question, pk=question_id)
    answers_ = paginate(request, question.answers.all(),
                        per_page=constants.ANSWERS_PER_PAGE)
    vocab = [t.name for t in Tag.objects.all()]  # TODO: Fetch only name.
    feed_urls = ((reverse('questions.answers.feed',
                          kwargs={'question_id': question_id}),
                  AnswersFeed().title(question)),)
    frequencies = dict(FREQUENCY_CHOICES)

    return {'question': question,
            'answers': answers_,
            'form': form or AnswerForm(),
            'answer_preview': answer_preview,
            'watch_form': watch_form or _init_watch_form(request, 'reply'),
            'feeds': feed_urls,
            'tag_vocab': json.dumps(vocab),
            'frequencies': frequencies,
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


# Initialize a WatchQuestionForm
def _init_watch_form(request, event_type='solution'):
    initial = {'event_type': event_type}
    if request.user.is_authenticated():
        initial['email'] = request.user.email
    return WatchQuestionForm(initial=initial)

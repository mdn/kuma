from django.conf.urls.defaults import patterns, url
from django.contrib.contenttypes.models import ContentType

from .feeds import QuestionsFeed, AnswersFeed, TaggedQuestionsFeed
from .models import Question, Answer
from flagit import views as flagit_views


urlpatterns = patterns('questions.views',
    url(r'^$', 'questions', name='questions.questions'),
    url(r'^/new$', 'new_question', name='questions.new_question'),
    url(r'^/(?P<question_id>\d+)/confirm/(?P<confirmation_id>\w+)$',
        'confirm_question_form', name='questions.confirm_form'),
    url(r'^/(?P<question_id>\d+)$', 'answers', name='questions.answers'),
    url(r'^/(?P<question_id>\d+)/edit$',
        'edit_question', name='questions.edit_question'),
    url(r'^/(?P<question_id>\d+)/reply$', 'reply', name='questions.reply'),
    url(r'^/(?P<question_id>\d+)/delete$', 'delete_question',
        name='questions.delete'),
    url(r'^/(?P<question_id>\d+)/lock$', 'lock_question',
        name='questions.lock'),
    url(r'^/(?P<question_id>\d+)/delete/(?P<answer_id>\d+)$',
        'delete_answer', name='questions.delete_answer'),
    url(r'^/(?P<question_id>\d+)/edit/(?P<answer_id>\d+)$', 'edit_answer',
        name='questions.edit_answer'),
    url(r'^/(?P<question_id>\d+)/solution/(?P<answer_id>\d+)$', 'solution',
        name='questions.solution'),
    url(r'^/(?P<question_id>\d+)/vote$', 'question_vote',
        name='questions.vote'),
    url(r'^/(?P<question_id>\d+)/vote/(?P<answer_id>\d+)$',
        'answer_vote', name='questions.answer_vote'),
    url(r'^/(?P<question_id>\d+)/add-tag$', 'add_tag',
        name='questions.add_tag'),
    url(r'^/(?P<question_id>\d+)/remove-tag$', 'remove_tag',
        name='questions.remove_tag'),
    url(r'^/(?P<question_id>\d+)/add-tag-async$', 'add_tag_async',
        name='questions.add_tag_async'),
    url(r'^/(?P<question_id>\d+)/remove-tag-async$', 'remove_tag_async',
        name='questions.remove_tag_async'),

    # Flag content ("Report this post")
    url(r'^/(?P<object_id>\d+)/flag$', flagit_views.flag,
        {'content_type': ContentType.objects.get_for_model(Question).id},
        name='questions.flag'),
    url(r'^/(?P<question_id>\d+)/flag/(?P<object_id>\d+)$', flagit_views.flag,
        {'content_type': ContentType.objects.get_for_model(Answer).id},
        name='questions.answer_flag'),

    # Subcribe by email
    url(r'^/(?P<question_id>\d+)/watch$', 'watch_question',
        name='questions.watch'),
    url(r'^/(?P<question_id>\d+)/unwatch$', 'unwatch_question',
        name='questions.unwatch'),

    # Feeds
    url(r'^/feed$', QuestionsFeed(), name='questions.feed'),
    url(r'^/(?P<question_id>\d+)/feed$', AnswersFeed(),
        name='questions.answers.feed'),
    url(r'^/tagged/(?P<tag_slug>[\w\-]+)/feed$', TaggedQuestionsFeed(),
        name='questions.tagged_feed'),
)

from django.conf.urls.defaults import patterns, url
from .feeds import QuestionsFeed, AnswersFeed

urlpatterns = patterns('questions.views',
    url(r'^$', 'questions', name='questions.questions'),
    url(r'^/new$', 'new_question', name='questions.new_question'),
    url(r'^/(?P<question_id>\d+)$', 'answers', name='questions.answers'),
    url(r'^/(?P<question_id>\d+)/reply$', 'reply', name='questions.reply'),
    url(r'^/(?P<question_id>\d+)/solution/(?P<answer_id>\d+)$', 'solution',
        name='questions.solution'),
    url(r'^/feed$', QuestionsFeed(), name='questions.feed'),
    url(r'^/(?P<question_id>\d+)/feed$', AnswersFeed(),
        name='questions.answers.feed'),
    url(r'^/(?P<question_id>\d+)/vote$', 'question_vote',
        name='questions.vote'),
    url(r'^/(?P<question_id>\d+)/vote/(?P<answer_id>\d+)$',
        'answer_vote', name='questions.answer_vote'),
)

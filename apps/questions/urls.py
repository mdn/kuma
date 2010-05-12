from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('questions.views',
    url(r'^$', 'question_forums', name='questions.question_forums'),
    url(r'^/(?P<forum_slug>[\w\-]+)$', 'questions',
        name='questions.questions'),
    url(r'^/(?P<forum_slug>[\w\-]+)/new$', 'new_question',
        name='questions.new_question'),
    url(r'^/(?P<forum_slug>[\w\-]+)/(?P<question_id>\d+)$', 'answers',
        name='questions.answers'),
    url(r'^/(?P<forum_slug>[\w\-]+)/(?P<question_id>\d+)/reply$',
        'reply', name='questions.reply'),
)

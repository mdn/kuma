from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('questions.views',
    url(r'^$', 'questions', name='questions.questions'),
    url(r'^/new$', 'new_question', name='questions.new_question'),
    url(r'^/(?P<question_id>\d+)$', 'answers', name='questions.answers'),
    url(r'^/(?P<question_id>\d+)/reply$', 'reply', name='questions.reply'),
    url(r'^/(?P<question_id>\d+)/solution/(?P<answer_id>\d+)$', 'solution',
        name='questions.solution'),
)

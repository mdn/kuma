from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django import newforms as forms
from django.http import Http404, HttpResponse
from exampleblog.models import BlogPost
from threadedcomments.models import ThreadedComment, MARKDOWN
from voting.models import Vote
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

class PostForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea)
    next = forms.CharField(widget=forms.HiddenInput)
    markup = forms.IntegerField(widget=forms.HiddenInput)

def comment_partial(request, comment_id):
    depth = 0
    comment = ThreadedComment.objects.get(id=comment_id)
    depth_probe = comment
    while depth_probe.parent != None:
        depth = depth + 1
        depth_probe = depth_probe.parent
    context = {
        'comment' : comment,
        'depth' : depth,
        'score' : Vote.objects.get_score(comment),
        'vote' : Vote.objects.get_for_user(comment, request.user),
    }
    return render_to_response('exampleblog/comment_partial.html', context, context_instance=RequestContext(request))
#comment_partial = login_required(comment_partial)

def latest_post(request):
    post = BlogPost.objects.latest('date_posted')
    comments = ThreadedComment.public.get_tree(post)
    scores = Vote.objects.get_scores_in_bulk(comments)
    uservotes = Vote.objects.get_for_user_in_bulk(comments, request.user)
    c_and_s = [(c,scores.get(c.pk,{'score':0,'num_votes':0}),uservotes.get(c.pk,{'is_upvote' : False, 'is_downvote' : False})) for c in comments]
    init_data = {
        'next' : reverse('exampleblog_latest'),
        'markup' : MARKDOWN,
    }
    context = {
        'post' : post,
        'comments_and_scores' : c_and_s,
        'form' : PostForm(initial=init_data),
    }
    return render_to_response('exampleblog/latest.html', context, context_instance=RequestContext(request))
#latest_post = login_required(latest_post)

class RegistrationForm(forms.Form):
    username = forms.CharField(min_length = 3, max_length = 128)
    password = forms.CharField(min_length = 4, max_length = 128);

def register(request):
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        try:
            check = User.objects.get(username = form.cleaned_data['username'])
            raise Http404
        except User.DoesNotExist:
            pass
        u = User(username = form.cleaned_data['username'], is_active = True)
        u.set_password(form.cleaned_data['password'])
        u.save()
        authed_user = authenticate(username = form.cleaned_data['username'], password = form.cleaned_data['password'])
        if not authed_user:
            raise Http404
        login(request, authed_user)
        return HttpResponse('Success')
    raise Http404

def auth_login(request):
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        authed_user = authenticate(username = form.cleaned_data['username'], password = form.cleaned_data['password'])
        if authed_user:
            login(request, authed_user)
            return HttpResponse('Success')
    raise Http404

def check_exists(request):
    username = request.GET.get('username', None)
    if username:
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            return HttpResponse("Does Not Exist")
    raise Http404
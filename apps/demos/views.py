import jingo
import logging
import random

from django.conf import settings
from django.core.cache import cache

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden

from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from django.contrib.auth.views import AuthenticationForm 
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from django.utils.translation import ugettext_lazy as _

from django.views.generic.list_detail import object_list
from tagging.views import tagged_object_list

from devmo import (SECTION_USAGE, SECTION_ADDONS, SECTION_APPS, SECTION_MOBILE,
                   SECTION_WEB)
from feeder.models import Bundle, Feed

from django.contrib.auth.models import User
from devmo.models import UserProfile

from tagging.models import Tag, TaggedItem
from tagging.utils import LINEAR, LOGARITHMIC

from demos.models import Submission
from demos.forms import SubmissionNewForm, SubmissionEditForm
from . import DEMOS_CACHE_NS_KEY

from contentflagging.models import ContentFlag
from contentflagging.forms import ContentFlagForm

import threadedcomments.views
from threadedcomments.models import ThreadedComment
from threadedcomments.forms import ThreadedCommentForm

from utils import JingoTemplateLoader
template_loader = JingoTemplateLoader()

DEMOS_PAGE_SIZE = getattr(settings, 'DEMOS_PAGE_SIZE', 24)
DEMOS_LAST_NEW_COMMENT_ID = 'demos_last_new_comment_id'

def home(request):
    """Home page."""

    featured_submissions = Submission.objects.order_by('-modified').filter(featured=True)
    if not Submission.allows_listing_hidden_by(request.user):
        featured_submissions = featured_submissions.exclude(hidden=True)

    submissions = Submission.objects.all_sorted(request.GET.get('sort', 'created'))
    if not Submission.allows_listing_hidden_by(request.user):
        submissions = submissions.exclude(hidden=True)

    return object_list(request, submissions,
        extra_context={
            'featured_submission_list': featured_submissions,
        },
        paginate_by=DEMOS_PAGE_SIZE, allow_empty=True,
        template_loader=template_loader,
        template_object_name='submission',
        template_name='demos/home.html') 

def detail(request, slug):
    """Detail page for a submission"""
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_viewing_by(request.user):
        return HttpResponseForbidden(_('access denied')+'')

    last_new_comment_id = request.session.get(DEMOS_LAST_NEW_COMMENT_ID, None)
    if last_new_comment_id:
        del request.session[DEMOS_LAST_NEW_COMMENT_ID]

    more_by = Submission.objects.filter(creator=submission.creator)\
            .exclude(hidden=True)\
            .order_by('-modified').all()[:5]
    
    return jingo.render(request, 'demos/detail.html', {
        'submission': submission,
        'last_new_comment_id': last_new_comment_id,
        'more_by': more_by 
    })

def all(request):
    """Browse all demo submissions"""
    sort_order = request.GET.get('sort', 'created')
    queryset = Submission.objects.all_sorted(sort_order)\
            .exclude(hidden=True)
    return object_list(request, queryset,
        paginate_by=DEMOS_PAGE_SIZE, allow_empty=True,
        template_loader=template_loader,
        template_object_name='submission',
        template_name='demos/listing_all.html') 

def tag(request, tag):
    sort_order = request.GET.get('sort', 'created')
    queryset = Submission.objects.all_sorted(sort_order)\
            .exclude(hidden=True)

    return tagged_object_list(request,
        queryset_or_model=queryset, tag=tag,
        paginate_by=DEMOS_PAGE_SIZE, allow_empty=True, 
        template_loader=template_loader,
        template_object_name='submission',
        template_name='demos/listing_tag.html')

def search(request):
    """Search against submission title, summary, and description"""
    query_string = request.GET.get('q', '')
    sort_order = request.GET.get('sort', 'created')
    queryset = Submission.objects.search(query_string, sort_order)\
            .exclude(hidden=True)
    return object_list(request, queryset,
        paginate_by=DEMOS_PAGE_SIZE, allow_empty=True,
        template_loader=template_loader,
        template_object_name='submission',
        template_name='demos/listing_search.html') 

def profile_detail(request, username):
    user = get_object_or_404(User, username=username)
    profile = UserProfile.objects.get(user=user)

    try:
        # HACK: This seems like a dirty violation of the DekiWiki auth package
        from dekicompat.backends import DekiUserBackend
        backend = DekiUserBackend()
        deki_user = backend.get_deki_user(profile.deki_user_id)
    except:
        deki_user = None

    sort_order = request.GET.get('sort', 'created')
    queryset = Submission.objects.all_sorted(sort_order)\
            .exclude(hidden=True)\
            .filter(creator=user)
    return object_list(request, queryset,
        extra_context=dict( 
            profile_user=user, 
            profile_deki_user=deki_user
        ),
        paginate_by=25, allow_empty=True,
        template_loader=template_loader,
        template_object_name='submission',
        template_name='demos/profile_detail.html') 

def like(request, slug):
    submission = get_object_or_404(Submission, slug=slug)
    if request.method == "POST":
        submission.likes.increment(request)
    if request.GET.get('iframe', False):
        # Use iframe event to update like button display to current state
        event = ( (submission.likes.get_total_for_request(request) > 0) 
            and 'liked' or 'unliked' )
        return jingo.render(request, 'demos/iframe_utils.html', dict(
            submission=submission, event=event
        ))
    return HttpResponseRedirect(reverse(
        'demos.views.detail', args=(submission.slug,)))

def unlike(request, slug):
    submission = get_object_or_404(Submission, slug=slug)
    if request.method == "POST":
        submission.likes.decrement(request)
    if request.GET.get('iframe', False):
        # Use iframe event to update like button display to current state
        event = ( (submission.likes.get_total_for_request(request) > 0) 
            and 'liked' or 'unliked' )
        return jingo.render(request, 'demos/iframe_utils.html', dict(
            submission=submission, event=event
        ))
    return HttpResponseRedirect(reverse(
        'demos.views.detail', args=(submission.slug,)))

def flag(request, slug):
    submission = get_object_or_404(Submission, slug=slug)

    if request.method != "POST":
        form = ContentFlagForm(request.GET)
    else:
        form = ContentFlagForm(request.POST, request.FILES)
        if form.is_valid():
            flag, created = ContentFlag.objects.flag(request=request, object=submission,
                    flag_type=form.cleaned_data['flag_type'],
                    explanation=form.cleaned_data['explanation'])
            return HttpResponseRedirect(reverse(
                'demos.views.detail', args=(submission.slug,)))

    return jingo.render(request, 'demos/flag.html', {
        'form': form, 'submission': submission })

def download(request, slug):
    """Demo download with action counting"""
    submission = get_object_or_404(Submission, slug=slug)
    return HttpResponseRedirect(submission.demo_package.url)

def launch(request, slug):
    """Demo launch view with action counting"""
    submission = get_object_or_404(Submission, slug=slug)
    submission.launches.increment(request)
    if submission.navbar_optout:
        return HttpResponseRedirect(
            submission.demo_package.url.replace('.zip', '/index.html'))
    else:
        return jingo.render(request, 'demos/launch.html', {
            'submission': submission })

def submit(request):
    """Accept submission of a demo"""
    if not request.user.is_authenticated():
        return jingo.render(request, 'demos/submit_noauth.html', {})

    if request.method != "POST":
        form = SubmissionNewForm()
    else:
        form = SubmissionNewForm(request.POST, request.FILES)
        if form.is_valid():
            
            new_sub = form.save(commit=False)
            if request.user.is_authenticated():
                new_sub.creator = request.user
            new_sub.save()
            ns_key = cache.get(DEMOS_CACHE_NS_KEY)
            if ns_key is None:
                ns_key = random.randint(1,10000)
                cache.set(DEMOS_CACHE_NS_KEY, ns_key)
            else:
                cache.incr(DEMOS_CACHE_NS_KEY)
            
            # TODO: Process in a cronjob?
            new_sub.process_demo_package()

            return HttpResponseRedirect(reverse(
                    'demos.views.detail', args=(new_sub.slug,)))

    return jingo.render(request, 'demos/submit.html', {'form': form})

def edit(request, slug):
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_editing_by(request.user):
        return HttpResponseForbidden(_('access denied')+'')

    if request.method != "POST":
        form = SubmissionEditForm(instance=submission)
    else:
        form = SubmissionEditForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():

            sub = form.save(commit=False)
            sub.save()
            
            # TODO: Process in a cronjob?
            sub.process_demo_package()
            
            return HttpResponseRedirect(reverse(
                    'demos.views.detail', args=(sub.slug,)))

    return jingo.render(request, 'demos/submit.html', { 
        'form': form, 'submission': submission, 'edit': True })

def delete(request, slug):
    """Delete a submission"""
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_deletion_by(request.user):
        return HttpResponseForbidden(_('access denied')+'')

    if request.method == "POST":
        submission.delete()
        return HttpResponseRedirect(reverse('demos.views.home'))

    return jingo.render(request, 'demos/delete.html', { 
        'submission': submission })

@login_required
def new_comment(request, slug, parent_id=None):
    """ """
    submission = get_object_or_404(Submission, slug=slug)
    model = ThreadedComment
    form_class = ThreadedCommentForm
    threadedcomments.views._adjust_max_comment_length(form_class)

    form = form_class(request.POST)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.ip_address = request.META.get('REMOTE_ADDR', None)
        new_comment.content_type = ContentType.objects.get_for_model(submission)
        new_comment.object_id = submission.id
        new_comment.user = request.user
        if parent_id:
            new_comment.parent = get_object_or_404(model, id = int(parent_id))
        new_comment.save()

        request.session[DEMOS_LAST_NEW_COMMENT_ID] = new_comment.id

    return HttpResponseRedirect(reverse(
        'demos.views.detail', args=(submission.slug,)))

def delete_comment(request, slug, object_id):
    """Delete a comment on a submission, if permitted."""
    tc = get_object_or_404(ThreadedComment, id=int(object_id))
    if not threadedcomments.views.can_delete_comment(tc, request.user):
        return HttpResponseForbidden(_('access denied')+'')
    submission = get_object_or_404(Submission, slug=slug)
    if request.method == "POST":
        tc.delete()
        return HttpResponseRedirect(reverse(
            'demos.views.detail', args=(submission.slug,)))
    return jingo.render(request, 'demos/delete_comment.html', { 
        'comment': tc 
    })

def hideshow(request, slug, hide=True):
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_hiding_by(request.user):
        return HttpResponseForbidden(_('access denied')+'')

    if request.method == "POST":
        submission.hidden = hide
        submission.save()

    return HttpResponseRedirect(reverse(
            'demos.views.detail', args=(submission.slug,)))

def terms(request):
    return jingo.render(request, 'demos/terms.html', {})

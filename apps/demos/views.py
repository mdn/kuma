import jingo
import logging
import random

from django.conf import settings
from django.core.cache import cache

from django.http import ( HttpResponseRedirect, HttpResponse,
        HttpResponseForbidden, HttpResponseNotFound )

from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from django.contrib.auth.views import AuthenticationForm 
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from django.utils.translation import ugettext_lazy as _

from django.views.generic.list_detail import object_list

from devmo import (SECTION_USAGE, SECTION_ADDONS, SECTION_APPS, SECTION_MOBILE,
                   SECTION_WEB)
from feeder.models import Bundle, Feed

from django.contrib.auth.models import User
from devmo.models import UserProfile

import constance.config

from taggit.models import Tag

from taggit_extras.utils import parse_tags, split_strip

from demos.models import Submission
from demos.forms import SubmissionNewForm, SubmissionEditForm

from . import DEMOS_CACHE_NS_KEY

from contentflagging.models import ContentFlag, FLAG_NOTIFICATIONS
from contentflagging.forms import ContentFlagForm

import threadedcomments.views
from threadedcomments.models import ThreadedComment
from threadedcomments.forms import ThreadedCommentForm

from utils import JingoTemplateLoader
template_loader = JingoTemplateLoader()

DEMOS_PAGE_SIZE = getattr(settings, 'DEMOS_PAGE_SIZE', 12)
DEMOS_LAST_NEW_COMMENT_ID = 'demos_last_new_comment_id'

# bug 657779: migrated from plain tags to tech:* tags for these:
KNOWN_TECH_TAGS = ( 
    "audio", "canvas", "css3", "device", "files", "fonts", "forms",
    "geolocation", "javascript", "html5", "indexeddb", "dragndrop",
    "mobile", "offlinesupport", "svg", "video", "webgl", "websockets",
    "webworkers", "xhr", "multitouch", 
)

def _invalidate_submission_listing_helper_cache():
    """Invalidate the cache for submission_listing helper used in templates"""
    # TODO: Does this belong in helpers.py? Better done with a model save event subscription?
    ns_key = cache.get(DEMOS_CACHE_NS_KEY)
    if ns_key is None:
        ns_key = random.randint(1,10000)
        cache.set(DEMOS_CACHE_NS_KEY, ns_key)
    else:
        cache.incr(DEMOS_CACHE_NS_KEY)

def home(request):
    """Home page."""
    featured_submissions = Submission.objects.filter(featured=True)\
        .exclude(hidden=True)\
        .order_by('-modified').all()[:3]

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
    submission = get_object_or_404(Submission.admin_manager, slug=slug)
    if submission.censored and submission.censored_url:
        return HttpResponseRedirect(submission.censored_url)
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
    """Tag view of demos"""

    # HACK: bug 657779 - migrated from plain tags to tech:* tags for these:
    if tag in KNOWN_TECH_TAGS:
        return HttpResponseRedirect(reverse(
            'demos.views.tag', args=('tech:%s' % tag,)))

    # Bounce to special-purpose Dev Derby tag page
    if tag.startswith('challenge:'):
        return HttpResponseRedirect(reverse(
            'demos.views.devderby_tag', args=(tag,)))

    tag_obj = get_object_or_404(Tag, name=tag)

    sort_order = request.GET.get('sort', 'created')
    queryset = Submission.objects.all_sorted(sort_order)\
            .filter(taggit_tags__name__in=[tag])\
            .exclude(hidden=True)

    return object_list(request, queryset, 
        paginate_by=DEMOS_PAGE_SIZE, allow_empty=True, 
        extra_context=dict( tag=tag_obj ),
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
    return HttpResponseRedirect(reverse(
        'devmo.views.profile_view', args=(username,)))

def like(request, slug):
    submission = get_object_or_404(Submission, slug=slug)
    if request.method == "POST":
        submission.likes.increment(request)
    return _like_feedback(request, submission, 'liked')

def unlike(request, slug):
    submission = get_object_or_404(Submission, slug=slug)
    if request.method == "POST":
        submission.likes.decrement(request)
    return _like_feedback(request, submission, 'unliked')

def _like_feedback(request, submission, event):
    if request.GET.get('iframe', False):
        response = jingo.render(request, 'demos/iframe_utils.html', dict(
            submission=submission, event=event
        ))
        response['x-frame-options'] = 'SAMEORIGIN'
        return response
    return HttpResponseRedirect(reverse(
        'demos.views.detail', args=(submission.slug,)))

def flag(request, slug):
    submission = get_object_or_404(Submission, slug=slug)

    if request.method != "POST":
        form = ContentFlagForm(request.GET)
    else:
        form = ContentFlagForm(request.POST, request.FILES)
        if form.is_valid():
            flag_type=form.cleaned_data['flag_type']
            recipients = None
            if flag_type in FLAG_NOTIFICATIONS and FLAG_NOTIFICATIONS[flag_type]:
                recipients = [profile.user.email for profile in UserProfile.objects.filter(content_flagging_email=True)]
            flag, created = ContentFlag.objects.flag(request=request, object=submission,
                    flag_type=flag_type,
                    explanation=form.cleaned_data['explanation'],
                    recipients=recipients)
            return HttpResponseRedirect(reverse(
                'demos.views.detail', args=(submission.slug,)))

    #TODO liberate?
    response = jingo.render(request, 'demos/flag.html', {
        'form': form, 'submission': submission })
    response['x-frame-options'] = 'SAMEORIGIN'
    return response

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
        initial = {}
        if 'tags' in request.GET:
            initial['challenge_tags'] = parse_tags(request.GET['tags'])
        form = SubmissionNewForm(initial=initial, request_user=request.user)
    else:
        form = SubmissionNewForm(request.POST, request.FILES, request_user=request.user)
        if form.is_valid():
            new_sub = form.save(commit=False)
            new_sub.creator = request.user
            new_sub.save()
            form.save_m2m()
            
            # TODO: Process in a cronjob?
            new_sub.process_demo_package()
            _invalidate_submission_listing_helper_cache()

            return HttpResponseRedirect(reverse(
                    'demos.views.detail', args=(new_sub.slug,)))

    return jingo.render(request, 'demos/submit.html', {'form': form})

def edit(request, slug):
    """Edit a demo"""
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_editing_by(request.user):
        return HttpResponseForbidden(_('access denied')+'')

    if request.method != "POST":
        form = SubmissionEditForm(instance=submission, request_user=request.user)
    else:
        form = SubmissionEditForm(request.POST, request.FILES, 
                instance=submission, request_user=request.user)
        if form.is_valid():

            sub = form.save()
            
            # TODO: Process in a cronjob?
            sub.process_demo_package()
            _invalidate_submission_listing_helper_cache()
            
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
        _invalidate_submission_listing_helper_cache()
        return HttpResponseRedirect(reverse('demos.views.home'))

    response = jingo.render(request, 'demos/delete.html', { 
        'submission': submission })
    response['x-frame-options'] = 'SAMEORIGIN'
    return response

@login_required
def new_comment(request, slug, parent_id=None):
    """Local reimplementation of threadedcomments new_comment"""
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
    response = jingo.render(request, 'demos/delete_comment.html', { 
        'comment': tc 
    })
    response['x-frame-options'] = 'SAMEORIGIN'
    return response

def hideshow(request, slug, hide=True):
    """Hide/show a demo"""
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_hiding_by(request.user):
        return HttpResponseForbidden(_('access denied')+'')

    if request.method == "POST":
        submission.hidden = hide
        submission.save()

    return HttpResponseRedirect(reverse(
            'demos.views.detail', args=(submission.slug,)))

def terms(request):
    """Terms of use page"""
    return jingo.render(request, 'demos/terms.html', {})

def devderby_landing(request):
    """Dev Derby landing page"""

    sort_order = request.GET.get('sort', 'created')

    # Grab current arrangement of challenges from Constance settings
    current_challenge_tag_name = str(
            constance.config.DEMOS_DEVDERBY_CURRENT_CHALLENGE_TAG).strip()
    previous_winner_tag_name = str(
            constance.config.DEMOS_DEVDERBY_PREVIOUS_WINNER_TAG).strip()
    previous_challenge_tag_names = parse_tags(
            constance.config.DEMOS_DEVDERBY_PREVIOUS_CHALLENGE_TAGS,
            sorted=False)
    challenge_choices = parse_tags(
            constance.config.DEMOS_DEVDERBY_CHALLENGE_CHOICE_TAGS,
            sorted=False)

    submissions_qs = (Submission.objects.all_sorted(sort_order)
        .filter(taggit_tags__name__in=[current_challenge_tag_name])
        .exclude(hidden=True))

    previous_winner_qs = (Submission.objects.all() 
        .filter(taggit_tags__name__in=[previous_winner_tag_name])
        .exclude(hidden=True))

    # TODO: Use an object_list here, in case we need pagination?
    return jingo.render(request, 'demos/devderby_landing.html', dict(
        current_challenge_tag_name = current_challenge_tag_name,
        previous_winner_tag_name = previous_winner_tag_name,
        previous_challenge_tag_names = previous_challenge_tag_names,
        submissions_qs = submissions_qs,
        previous_winner_qs = previous_winner_qs,
        challenge_choices = challenge_choices,
    ))

def devderby_rules(request):
    """Dev Derby rules page"""
    return jingo.render(request, 'demos/devderby_rules.html', {})

def devderby_by_date(request, year, month):
    """Friendly URL path to devderby tag.
    see: https://bugzilla.mozilla.org/show_bug.cgi?id=666460#c15
    """
    return devderby_tag(request, 'challenge:%s:%s' % ( year, month ))

def devderby_tag(request, tag):
    """Render a devderby-specific tag page with details on the derby and a
    showcase of winners, if any."""

    if not tag.startswith('challenge:'):
        return HttpResponseRedirect(reverse(
            'demos.views.tag', args=(tag,)))

    tag_obj = get_object_or_404(Tag, name=tag)

    # Assemble the demos submitted for the derby
    sort_order = request.GET.get('sort', 'created')
    queryset = Submission.objects.all_sorted(sort_order)\
            .filter(taggit_tags__name__in=[tag])\
            .exclude(hidden=True)

    # Search for the winners, tag by tag.
    # TODO: Do this all in one query, and sort here by winner place?
    winner_demos = []
    for name in ( 'firstplace', 'secondplace', 'thirdplace' ):
        
        # Look for the winner tag using our naming convention, eg.
        # system:challenge:firstplace:2011:june
        winner_tag_name = 'system:challenge:%s:%s' % ( 
            name, tag.replace('challenge:','')
        )

        # Grab only the first match for this tag. If there are others, we'll
        # just ignore them.
        demos = ( Submission.objects.all()
            .filter(taggit_tags__name__in=[winner_tag_name]) )
        for demo in demos:
            winner_demos.append(demo)

    return object_list(request, queryset, 
        paginate_by=DEMOS_PAGE_SIZE, allow_empty=True, 
        extra_context=dict( 
            tag=tag_obj, 
            winner_demos=winner_demos
        ),
        template_loader=template_loader,
        template_object_name='submission',
        template_name='demos/devderby_tag.html')

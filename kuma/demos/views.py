import random

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import ListView

from constance import config
from taggit.models import Tag

from kuma.contentflagging.models import ContentFlag, FLAG_NOTIFICATIONS
from kuma.contentflagging.forms import ContentFlagForm
from kuma.core.utils import parse_tags
from kuma.core.cache import memcache
from kuma.users.models import User

from . import DEMOS_CACHE_NS_KEY
from .models import Submission
from .forms import SubmissionNewForm, SubmissionEditForm

DEMOS_PAGE_SIZE = getattr(settings, 'DEMOS_PAGE_SIZE', 10)

# bug 657779: migrated from plain tags to tech:* tags for these:
KNOWN_TECH_TAGS = (
    "audio", "canvas", "css3", "device", "files", "fonts", "forms",
    "geolocation", "javascript", "html5", "indexeddb", "dragndrop",
    "mobile", "offlinesupport", "svg", "video", "webgl", "websockets",
    "webworkers", "xhr", "multitouch",
)


def _invalidate_submission_listing_helper_cache():
    """Invalidate the cache for submission_listing helper used in templates"""
    # TODO: Does this belong in helpers.py? Better done with a model save event
    # subscription?
    ns_key = memcache.get(DEMOS_CACHE_NS_KEY)
    if ns_key is None:
        ns_key = random.randint(1, 10000)
        memcache.set(DEMOS_CACHE_NS_KEY, ns_key)
    else:
        memcache.incr(DEMOS_CACHE_NS_KEY)


class HomeView(ListView):
    allow_empty = True
    context_object_name = 'submission_list'
    paginate_by = DEMOS_PAGE_SIZE
    template_name = 'demos/home.html'

    def get_queryset(self):
        submissions = Submission.objects.all_sorted(
            self.request.GET.get('sort', 'created'))
        if not Submission.allows_listing_hidden_by(self.request.user):
            submissions = submissions.exclude(hidden=True)
        return submissions

    def get_context_data(self, **kwargs):
        base_context = super(HomeView, self).get_context_data(**kwargs)
        featured = Submission.objects.all_sorted(sort='recentfeatured', max=3)
        base_context['featured_submission_list'] = featured
        base_context['is_demo_home'] = True
        return base_context


def detail(request, slug):
    """Detail page for a submission"""
    submission = get_object_or_404(Submission.admin_manager, slug=slug)
    if submission.censored and submission.censored_url:
        return redirect(submission.censored_url)
    if not submission.allows_viewing_by(request.user):
        return HttpResponseForbidden(_('access denied') + '')

    more_by = (Submission.objects.filter(creator=submission.creator)
                                 .exclude(hidden=True)
                                 .order_by('-modified').all()[:5])

    return render(request, 'demos/detail.html', {
        'submission': submission,
        'more_by': more_by
    })


class AllView(ListView):
    allow_empty = True
    context_object_name = 'submission_list'
    paginate_by = DEMOS_PAGE_SIZE
    template_name = 'demos/home.html'

    def get_queryset(self):
        sort_order = self.request.GET.get('sort', 'created')
        queryset = Submission.objects.all_sorted(sort_order)
        if not Submission.allows_listing_hidden_by(self.request.user):
            queryset = queryset.exclude(hidden=True)
        return queryset


class TagView(ListView):
    allow_empty = True
    context_object_name = 'submission_list'
    paginate_by = DEMOS_PAGE_SIZE
    template_name = 'demos/listing_tag.html'

    def get(self, request, *args, **kwargs):
        tag = kwargs['tag']
        get_object_or_404(Tag, name=tag)

        if tag in KNOWN_TECH_TAGS:
            return redirect('demos_tag', 'tech:%s' % tag)

        # Bounce to special-purpose Dev Derby tag page
        if tag.startswith('challenge:'):
            return redirect('demos_devderby_tag', tag)

        return super(TagView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        tag = self.kwargs['tag']
        sort_order = self.request.GET.get('sort', 'created')
        queryset = (Submission.objects.all_sorted(sort_order)
                                      .filter(taggit_tags__name__in=[tag])
                                      .exclude(hidden=True))
        return queryset

    def get_context_data(self, **kwargs):
        tag_obj = get_object_or_404(Tag, name=self.kwargs['tag'])
        base_context = super(TagView, self).get_context_data(**kwargs)
        base_context['tag'] = tag_obj
        return base_context


class DevDerbyTagView(ListView):
    allow_empty = True
    context_object_name = 'submission_list'
    paginate_by = DEMOS_PAGE_SIZE
    template_name = 'demos/listing_tag.html'

    def get(self, request, *args, **kwargs):
        tag = kwargs['tag']
        if not tag.startswith('challenge'):
            return redirect('demos_tag', tag)
        return super(DevDerbyTagView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        tag = self.kwargs['tag']
        sort_order = self.request.GET.get('sort', 'created')
        return (Submission.objects.all_sorted(sort_order)
                                  .filter(taggit_tags__name__in=[tag])
                                  .exclude(hidden=True))

    def get_context_data(self, **kwargs):
        tag = self.kwargs['tag']
        tag_obj = get_object_or_404(Tag, name=tag)
        winner_demos = []
        for name in ('firstplace', 'secondplace', 'thirdplace'):
            # Look for the winner tag using our naming convention, eg.
            # system:challenge:firstplace:2011:june
            winner_tag_name = 'system:challenge:%s:%s' % (
                name, tag.replace('challenge:', '')
            )

            # Grab only the first match for this tag. If there are others, we'll
            # just ignore them.
            demos = (Submission.objects.all()
                     .filter(taggit_tags__name__in=[winner_tag_name]))
            for demo in demos:
                winner_demos.append(demo)
        base_context = super(DevDerbyTagView, self).get_context_data(**kwargs)
        base_context['tag'] = tag_obj
        base_context['winner_demos'] = winner_demos
        return base_context


class DevDerbyByDate(DevDerbyTagView):
    def get(self, request, *args, **kwargs):
        year = kwargs['year']
        month = kwargs['month']
        self.kwargs['tag'] = 'challenge:%s:%s' % (year, month)
        return super(DevDerbyByDate, self).get(request,
                                               tag=self.kwargs['tag'])


class SearchView(ListView):
    allow_empty = True
    context_object_name = 'submission_list'
    paginate_by = DEMOS_PAGE_SIZE
    template_name = 'demos/listing_search.html'

    def get_queryset(self):
        query_string = self.request.GET.get('q', '')
        sort_order = self.request.GET.get('sort', 'created')
        queryset = (Submission.objects.search(query_string, sort_order)
                                      .exclude(hidden=True))
        return queryset


def profile_detail(request, username):
    return redirect('users.user_detail', username)


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


@xframe_options_sameorigin
def _like_feedback(request, submission, event):
    if request.GET.get('iframe', False):
        return render(request, 'demos/iframe_utils.html', dict(
            submission=submission, event=event
        ))
    return redirect(submission)


@xframe_options_sameorigin
def flag(request, slug):
    submission = get_object_or_404(Submission, slug=slug)

    if request.method != "POST":
        form = ContentFlagForm(request.GET)
    else:
        form = ContentFlagForm(request.POST, request.FILES)
        if form.is_valid():
            flag_type = form.cleaned_data['flag_type']
            recipients = None
            if (flag_type in FLAG_NOTIFICATIONS and
                    FLAG_NOTIFICATIONS[flag_type]):
                recipients = list(User.objects.filter(content_flagging_email=True)
                                              .values_list('email', flat=True))
            flag, created = ContentFlag.objects.flag(
                request=request, object=submission,
                flag_type=flag_type,
                explanation=form.cleaned_data['explanation'],
                recipients=recipients)
            return redirect(submission)

    return render(request, 'demos/flag.html', {
        'form': form, 'submission': submission})


def download(request, slug):
    """Demo download with action counting"""
    submission = get_object_or_404(Submission, slug=slug)
    return redirect(submission.demo_package.url)


def launch(request, slug):
    """Demo launch view with action counting"""
    submission = get_object_or_404(Submission, slug=slug)
    submission.launches.increment(request)
    if submission.navbar_optout:
        return redirect(submission.demo_package.url.replace('.zip', '/index.html'))
    else:
        return render(request, 'demos/launch.html', {
            'submission': submission})


def submit(request):
    """Accept submission of a demo"""
    if not request.user.is_authenticated():
        return render(request, 'demos/submit_noauth.html')

    if request.method != "POST":
        initial = {}
        if 'tags' in request.GET:
            initial['challenge_tags'] = parse_tags(request.GET['tags'])
        form = SubmissionNewForm(initial=initial, request_user=request.user)
    else:
        form = SubmissionNewForm(
            request.POST, request.FILES, request_user=request.user)
        if form.is_valid():
            new_sub = form.save(commit=False)
            new_sub.creator = request.user
            new_sub.save()
            form.save_m2m()

            # TODO: Process in a cronjob?
            new_sub.process_demo_package()
            _invalidate_submission_listing_helper_cache()

            return redirect(new_sub)

    return render(request, 'demos/submit.html', {'form': form})


def edit(request, slug):
    """Edit a demo"""
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_managing_by(request.user):
        return HttpResponseForbidden(_('access denied') + '')

    if request.method != "POST":
        form = SubmissionEditForm(
            instance=submission, request_user=request.user)
    else:
        form = SubmissionEditForm(request.POST, request.FILES,
                                  instance=submission,
                                  request_user=request.user)
        if form.is_valid():

            sub = form.save()

            # TODO: Process in a cronjob?
            sub.process_demo_package()
            _invalidate_submission_listing_helper_cache()

            return redirect(sub)

    return render(request, 'demos/submit.html', {
        'form': form, 'submission': submission, 'edit': True})


@xframe_options_sameorigin
def delete(request, slug):
    """Delete a submission"""
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_managing_by(request.user):
        return HttpResponseForbidden(_('access denied') + '')

    if request.method == "POST":
        submission.delete()
        _invalidate_submission_listing_helper_cache()
        return redirect('demos')

    return render(request, 'demos/delete.html', {
        'submission': submission})


def hideshow(request, slug, hide=True):
    """Hide/show a demo"""
    submission = get_object_or_404(Submission, slug=slug)
    if not submission.allows_managing_by(request.user):
        return HttpResponseForbidden(_('access denied') + '')

    if request.method == "POST":
        submission.hidden = hide
        submission.save()

    return redirect(submission)


def terms(request):
    """Terms of use page"""
    return render(request, 'demos/terms.html', {})


def devderby_landing(request):
    """Dev Derby landing page"""

    sort_order = request.GET.get('sort', 'created')

    # Grab current arrangement of challenges from Constance settings
    current_challenge_tag_name = str(
        config.DEMOS_DEVDERBY_CURRENT_CHALLENGE_TAG).strip()
    previous_winner_tag_name = str(
        config.DEMOS_DEVDERBY_PREVIOUS_WINNER_TAG).strip()
    previous_challenge_tag_names = parse_tags(
        config.DEMOS_DEVDERBY_PREVIOUS_CHALLENGE_TAGS,
        sorted=False)
    challenge_choices = parse_tags(
        config.DEMOS_DEVDERBY_CHALLENGE_CHOICE_TAGS,
        sorted=False)

    submissions_qs = (Submission.objects.all_sorted(sort_order)
                                .filter(taggit_tags__name__in=[current_challenge_tag_name])
                                .exclude(hidden=True))

    previous_winner_qs = (Submission.objects.all()
                                    .filter(taggit_tags__name__in=[previous_winner_tag_name])
                                    .exclude(hidden=True))

    # TODO: Use an object_list here, in case we need pagination?
    return render(request, 'demos/devderby_landing.html', dict(
        current_challenge_tag_name=current_challenge_tag_name,
        previous_winner_tag_name=previous_winner_tag_name,
        previous_challenge_tag_names=previous_challenge_tag_names,
        submissions_qs=submissions_qs,
        previous_winner_qs=previous_winner_qs,
        challenge_choices=challenge_choices,
    ))


def devderby_rules(request):
    """Dev Derby rules page"""
    return render(request, 'demos/devderby_rules.html', {})

import json
from datetime import datetime, timedelta

from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.socialaccount import helpers
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.views import ConnectionsView
from allauth.socialaccount.views import SignupView as BaseSignupView
from constance import config
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import validate_email, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from honeypot.decorators import verify_honeypot_value
from taggit.utils import parse_tags

from kuma.core.decorators import (ensure_wiki_domain, login_required,
                                  redirect_in_maintenance_mode)
from kuma.wiki.forms import RevisionAkismetSubmissionSpamForm
from kuma.wiki.models import (Document, DocumentDeletionLog, Revision,
                              RevisionAkismetSubmission)

from .forms import (
    UserBanForm,
    UserDeleteForm,
    UserEditForm,
    UserRecoveryEmailForm)
from .models import User, UserBan
# we have to import the signup form here due to allauth's odd form subclassing
# that requires providing a base form class (see ACCOUNT_SIGNUP_FORM_CLASS)
from .signup import SignupForm


# TODO: Make this dynamic, editable from admin interface
INTEREST_SUGGESTIONS = [
    "audio", "canvas", "css3", "device", "files", "fonts",
    "forms", "geolocation", "javascript", "html5", "indexeddb", "dragndrop",
    "mobile", "offlinesupport", "svg", "video", "webgl", "websockets",
    "webworkers", "xhr", "multitouch",

    "front-end development",
    "web development",
    "tech writing",
    "user experience",
    "design",
    "technical review",
    "editorial review",
]


@ensure_wiki_domain
@permission_required('users.add_userban')
def ban_user(request, username):
    """
    Ban a user.
    """
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = UserBanForm(data=request.POST)
        if form.is_valid():
            ban = UserBan(user=user,
                          by=request.user,
                          reason=form.cleaned_data['reason'],
                          is_active=True)
            ban.save()
            return redirect(user)
    else:
        if user.active_ban:
            return redirect(user)
        form = UserBanForm()
    # A list of common reasons for banning a user, loaded from constance
    try:
        common_reasons = json.loads(config.COMMON_REASONS_TO_BAN_USERS)
    except (TypeError, ValueError):
        common_reasons = ['Spam']
    else:
        if not common_reasons:
            common_reasons = ['Spam']
    return render(request,
                  'users/ban_user.html',
                  {'form': form,
                   'detail_user': user,
                   'common_reasons': common_reasons})


@ensure_wiki_domain
@permission_required('users.add_userban')
def ban_user_and_cleanup(request, username):
    """
    A page to ban a user for the reason of "Spam" and mark the user's revisions
    and page creations as spam, reverting as many of them as possible.
    """
    user = get_object_or_404(User, username=username)

    # Is this user already banned?
    user_ban = UserBan.objects.filter(user=user, is_active=True)

    # Get revisions for the past 3 days for this user
    date_three_days_ago = datetime.now().date() - timedelta(days=3)
    revisions = user.created_revisions.prefetch_related('document')
    revisions = revisions.defer('content', 'summary').order_by('-id')
    revisions = revisions.filter(created__gte=date_three_days_ago)
    revisions_not_spam = revisions.filter(akismet_submissions=None)

    return render(request,
                  'users/ban_user_and_cleanup.html',
                  {'detail_user': user,
                   'user_banned': user_ban,
                   'revisions': revisions,
                   'revisions_not_spam': revisions_not_spam,
                   'on_ban_page': True})


@ensure_wiki_domain
@require_POST
@permission_required('users.add_userban')
def ban_user_and_cleanup_summary(request, username):
    """
    A summary page of actions taken when banning a user and reverting revisions
    This method takes all the revisions from the last three days,
    sends back the list of revisions that were successfully reverted/deleted
    and submitted to Akismet, and also a list of
    revisions where no action was taken (revisions needing follow up).
    """
    user = get_object_or_404(User, username=username)

    # Is this user already banned?
    user_ban = UserBan.objects.filter(user=user, is_active=True)

    # If the user is not banned, ban user; else, update 'by' and 'reason'
    if not user_ban.exists():
        ban = UserBan(user=user,
                      by=request.user,
                      reason='Spam',
                      is_active=True)
        ban.save()
    else:
        user_ban.update(by=request.user, reason='Spam')

    date_three_days_ago = datetime.now().date() - timedelta(days=3)
    revisions_from_last_three_days = user.created_revisions.prefetch_related('document')
    revisions_from_last_three_days = revisions_from_last_three_days.defer('content', 'summary').order_by('-id')
    revisions_from_last_three_days = revisions_from_last_three_days.filter(created__gte=date_three_days_ago)

    """ The "Actions Taken" section """
    # The revisions to be submitted to Akismet and reverted,
    # these must be sorted descending so that they are reverted accordingly
    revisions_to_mark_as_spam_and_revert = revisions_from_last_three_days.filter(
        id__in=request.POST.getlist('revision-id')).order_by('-id')

    # 1. Submit revisions to Akismet as spam
    # 2. If this is the most recent revision for a document:
    #    Revert revision if it has a previous version OR
    #    Delete revision if it is a new document
    submitted_to_akismet = []
    not_submitted_to_akismet = []
    revisions_reverted_list = []
    revisions_not_reverted_list = []
    revisions_deleted_list = []
    revisions_not_deleted_list = []
    latest_is_not_spam = [
        rev for rev in revision_by_distinct_doc(revisions_to_mark_as_spam_and_revert)
        if rev.document.current_revision != rev
    ]
    previous_good_rev = {}

    for revision in revisions_to_mark_as_spam_and_revert:
        submission = RevisionAkismetSubmission(sender=request.user, type="spam")
        akismet_submission_data = {'revision': revision.id}

        data = RevisionAkismetSubmissionSpamForm(
            data=akismet_submission_data,
            instance=submission,
            request=request)
        # Submit to Akismet or note that validation & sending to Akismet failed
        if data.is_valid():
            data.save()
            # Since we only want to display 1 revision per document, only add to
            # this list if this is one of the revisions for a distinct document
            submitted_to_akismet.append(revision)
        else:
            not_submitted_to_akismet.append(revision)

        # If there is a current revision and the revision is not in the spam list,
        # to be reverted, do not revert any revisions
        try:
            revision.document.refresh_from_db(fields=['current_revision'])
        except Document.DoesNotExist:
            continue  # This document was previously deleted in this loop, continue
        if revision.document.current_revision not in revisions_to_mark_as_spam_and_revert:
            if revision.document_id not in previous_good_rev:
                previous_good_rev[revision.document_id] = revision.document.current_revision

            continue  # This document has a more current revision, no need to revert

        # Loop through all previous revisions to find the oldest spam
        # revision on a specific document from this request.
        while revision.previous in revisions_to_mark_as_spam_and_revert:
            revision = revision.previous
        # If this is a new revision on an existing document, revert it
        if revision.previous:
            previous_good_rev[revision.document_id] = revision.previous

            reverted = revert_document(request=request,
                                       revision_id=revision.previous.id)
            if reverted:
                revisions_reverted_list.append(revision)
            else:
                # If the revert was unsuccessful, include this in the follow-up list
                revisions_not_reverted_list.append(revision)

        # If this is a new document/translation, delete it
        else:
            deleted = delete_document(request=request,
                                      document=revision.document)
            if deleted:
                revisions_deleted_list.append(revision)
            else:
                # If the delete was unsuccessful, include this in the follow-up list
                revisions_not_deleted_list.append(revision)

    # Find just the latest revision for each document
    submitted_to_akismet_by_distinct_doc = revision_by_distinct_doc(submitted_to_akismet)
    not_submitted_to_akismet_by_distinct_doc = revision_by_distinct_doc(not_submitted_to_akismet)
    revisions_reverted_by_distinct_doc = revision_by_distinct_doc(revisions_reverted_list)
    revisions_not_reverted_by_distinct_doc = revision_by_distinct_doc(revisions_not_reverted_list)
    revisions_deleted_by_distinct_doc = revision_by_distinct_doc(revisions_deleted_list)
    revisions_not_deleted_by_distinct_doc = revision_by_distinct_doc(revisions_not_deleted_list)

    actions_taken = {
        'revisions_reported_as_spam': submitted_to_akismet_by_distinct_doc,
        'revisions_reverted_list': revisions_reverted_by_distinct_doc,
        'revisions_deleted_list': revisions_deleted_by_distinct_doc
    }

    """ The "Needs followup" section """
    # TODO: Phase V: If user made actions while reviewer was banning them
    new_action_by_user = []
    skipped_revisions = [rev for rev in revisions_to_mark_as_spam_and_revert
                         if rev.document_id in previous_good_rev and
                         rev.id < previous_good_rev[rev.document_id].id]
    skipped_revisions = revision_by_distinct_doc(skipped_revisions)

    needs_follow_up = {
        'manual_revert': new_action_by_user,
        'skipped_revisions': skipped_revisions,
        'not_submitted_to_akismet': not_submitted_to_akismet_by_distinct_doc,
        'not_reverted_list': revisions_not_reverted_by_distinct_doc,
        'not_deleted_list': revisions_not_deleted_by_distinct_doc
    }

    """ The "No Actions Taken" section """
    revisions_already_spam = revisions_from_last_three_days.filter(
        id__in=request.POST.getlist('revision-already-spam')
    )
    revisions_already_spam = list(revisions_already_spam)
    revisions_already_spam_by_distinct_doc = revision_by_distinct_doc(revisions_already_spam)

    identified_as_not_spam = [rev for rev in revisions_from_last_three_days
                              if rev not in revisions_already_spam and
                              rev not in revisions_to_mark_as_spam_and_revert]
    identified_as_not_spam_by_distinct_doc = revision_by_distinct_doc(identified_as_not_spam)

    no_actions_taken = {
        'latest_revision_is_not_spam': latest_is_not_spam,
        'revisions_already_identified_as_spam': revisions_already_spam_by_distinct_doc,
        'revisions_identified_as_not_spam': identified_as_not_spam_by_distinct_doc
    }

    context = {'detail_user': user,
               'form': UserBanForm(),
               'actions_taken': actions_taken,
               'needs_follow_up': needs_follow_up,
               'no_actions_taken': no_actions_taken}

    # Send an email to the spam watch mailing list.
    ban_and_revert_notification(user, request.user, context)

    return render(request,
                  'users/ban_user_and_cleanup_summary.html',
                  context)


def revision_by_distinct_doc(list_of_revisions):
    documents = {}
    for rev in list_of_revisions:
        documents.setdefault(rev.document_id, rev)
        if documents[rev.document_id].id < rev.id:
            documents[rev.document_id] = rev

    return [documents[doc_id] for doc_id in sorted(documents)]


def ban_and_revert_notification(spammer, moderator, info):
    subject = '[MDN] %s has been banned by %s' % (spammer, moderator)
    context = {'spammer': spammer,
               'moderator': moderator}
    context.update(info)
    body = render_to_string('wiki/email/spam_ban.ltxt', context)

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
              [config.EMAIL_LIST_SPAM_WATCH])


@permission_required('users.add_userban')
def revert_document(request, revision_id):
    """
    Revert document to a specific revision.
    """
    revision = get_object_or_404(Revision.objects.select_related('document'),
                                 pk=revision_id)

    comment = "spam"
    document = revision.document
    old_revision_pk = revision.pk
    try:
        new_revision = document.revert(revision, request.user, comment)
        # schedule a rendering of the new revision if it really was saved
        if new_revision.pk != old_revision_pk:  # pragma: no branch
            document.schedule_rendering('max-age=0')
    except IntegrityError:
        return False
    return True


@permission_required('wiki.delete_document')
def delete_document(request, document):
    """
    Delete a Document.
    """
    try:
        DocumentDeletionLog.objects.create(
            locale=document.locale,
            slug=document.slug,
            user=request.user,
            reason='Spam',
        )
        document.delete()
    except Exception:
        return False
    return True


def user_detail(request, username):
    """
    The main user view that only collects a bunch of user
    specific data to populate the template context.
    """
    detail_user = get_object_or_404(User, username=username)

    if (detail_user.active_ban and not request.user.has_perm('users.add_userban')):
        return render(request, '404.html', {"reason": "banneduser"}, status=404)

    context = {'detail_user': detail_user}
    return render(request, 'users/user_detail.html', context)


@login_required
def my_detail_page(request):
    return redirect(request.user)


@login_required
def my_edit_page(request):
    return redirect('users.user_edit', request.user.username)


@redirect_in_maintenance_mode
def user_edit(request, username):
    """
    View and edit user profile
    """
    edit_user = get_object_or_404(User, username=username)

    if not edit_user.allows_editing_by(request.user):
        return HttpResponseForbidden()

    # Map of form field names to tag namespaces
    field_to_tag_ns = (
        ('interests', 'profile:interest:'),
        ('expertise', 'profile:expertise:')
    )

    revisions = Revision.objects.filter(creator=edit_user)

    if request.method != 'POST':
        initial = {
            'beta': edit_user.is_beta_tester,
            'username': edit_user.username,
            'is_github_url_public': edit_user.is_github_url_public,
        }

        # Form fields to receive tags filtered by namespace.
        for field, ns in field_to_tag_ns:
            initial[field] = ', '.join(tag.name.replace(ns, '')
                                       for tag in edit_user.tags.all_ns(ns))

        # Finally, set up the forms.
        user_form = UserEditForm(instance=edit_user,
                                 initial=initial,
                                 prefix='user')
    else:
        user_form = UserEditForm(data=request.POST,
                                 files=request.FILES,
                                 instance=edit_user,
                                 prefix='user')

        if user_form.is_valid():
            new_user = user_form.save()

            try:
                # Beta
                beta_group = Group.objects.get(name=config.BETA_GROUP_NAME)
                if user_form.cleaned_data['beta']:
                    beta_group.user_set.add(request.user)
                else:
                    beta_group.user_set.remove(request.user)
            except Group.DoesNotExist:
                # If there's no Beta Testers group, ignore that logic
                pass

            # Update tags from form fields
            for field, tag_ns in field_to_tag_ns:
                field_value = user_form.cleaned_data.get(field, '')
                tags = parse_tags(field_value)
                new_user.tags.set_ns(tag_ns, *tags)

            return redirect(edit_user)

    context = {
        'edit_user': edit_user,
        'user_form': user_form,
        'username': user_form['username'].value(),
        'form': UserDeleteForm(),
        'INTEREST_SUGGESTIONS': INTEREST_SUGGESTIONS,
        'revisions': revisions,
    }
    return render(request, 'users/user_edit.html', context)


@redirect_in_maintenance_mode
@login_required
def user_delete(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return HttpResponseForbidden()

    def donate_attributions():
        anon, _ = User.objects.get_or_create(username='Anonymous')
        user.created_revisions.update(creator=anon)
        user.created_attachment_revisions.update(creator=anon)

    def scrub_user():
        # From the User abstract class
        user.first_name = ''
        user.last_name = ''
        user.email = ''

        # All User attributes
        user.timezone = ''
        user.locale = ''
        user.homepage = ''
        user.title = ''
        user.fullname = ''
        user.organization = ''
        user.location = ''
        user.bio = ''
        user.irc_nickname = ''
        user.website_url = ''
        user.github_url = ''
        user.mozillians_url = ''
        user.twitter_url = ''
        user.linkedin_url = ''
        user.facebook_url = ''
        user.stackoverflow_url = ''
        user.discourse_url = ''
        user.stripe_customer_id = ''
        user.save()

        user.socialaccount_set.all().delete()
        user.key_set.all().delete()

    def force_logout():
        request.session.clear()

    def delete_user():
        # Protected references to users need to be manually deleted first.
        user.key_set.all().delete()

        # Some records are worth keeping prior to deleting the user
        # but "re-assign" to the anonymous user.
        anon, _ = User.objects.get_or_create(username='Anonymous')
        user.revisionakismetsubmission_set.update(sender=anon)
        user.documentdeletionlog_set.update(user=anon)
        user.documentspamattempt_set.update(user=anon)
        user.documentspam_reviewed.update(reviewer=anon)
        user.bans.update(user=anon)
        user.bans_issued.update(by=anon)

        user.delete()

    revisions = Revision.objects.filter(creator=request.user)
    context = {}
    if request.method == 'POST':
        # If the user has no revisions there's not choices on the form.
        if revisions.exists():
            form = UserDeleteForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    if form.cleaned_data['attributions'] == 'donate':
                        donate_attributions()
                        delete_user()
                    elif form.cleaned_data['attributions'] == 'keep':
                        scrub_user()
                        force_logout()
                    else:
                        raise NotImplementedError(
                            form.cleaned_data['attributions'])
                    return HttpResponseRedirect('/')

        else:
            delete_user()
            return HttpResponseRedirect('/')
    else:
        form = UserDeleteForm()

    context['form'] = form
    context['username'] = username
    context['revisions'] = revisions

    return render(request, 'users/user_delete.html', context)


def signin_landing(request):
    if not settings.MULTI_AUTH_ENABLED:
        raise Http404("Multi-auth is not enabled.")
    return render(request, "socialaccount/signup-landing.html")


class SignupView(BaseSignupView):
    """
    The default signup view from the allauth account app.

    You can remove this class if there is no other modification compared
    to it's parent class.
    """
    form_class = SignupForm

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        self.default_email = None
        self.email_addresses = {}
        form = super(SignupView, self).get_form(form_class)
        form.fields['email'].label = _('Email address')

        User = get_user_model()

        # When no username is provided, default to the local-part of the email address
        if form.initial.get('username', '') == '':
            email = form.initial.get('email', '')
            if isinstance(email, tuple):
                email = email[0]
            suggested_username = suggested_username_base = email.split('@')[0]
            increment = 1
            while User.objects.filter(username__iexact=suggested_username).exists():
                increment += 1
                suggested_username = f'{suggested_username_base}{increment}'
            form.initial['username'] = suggested_username

        self.matching_user = None
        initial_username = form.initial.get('username', None)

        # For GitHub/Google users, see if we can find matching user by username
        assert self.sociallogin.account.provider in ('github', 'google')
        try:
            self.matching_user = User.objects.get(username=initial_username)
            # deleting the initial username because we found a matching user
            del form.initial['username']
        except User.DoesNotExist:
            pass

        email = self.sociallogin.account.extra_data.get('email') or None
        email_data = (self.sociallogin.account.extra_data.get(
                      'email_addresses')) or []

        # Discard email addresses that won't validate
        extra_email_addresses = []
        for data in email_data:
            try:
                validate_email(data['email'])
            except ValidationError:
                pass
            else:
                extra_email_addresses.append(data)

        # if we didn't get any extra email addresses from the provider
        # but the default email is available, simply hide the form widget
        if not extra_email_addresses and email is not None:
            self.default_email = email

        # let the user choose from provider's extra email addresses, or enter
        # a new one.
        else:
            # build a mapping of the email addresses to their other values
            # to be used later for resetting the social accounts email addresses
            for email_address in extra_email_addresses:
                self.email_addresses[email_address['email']] = email_address

            # build the choice list with the given email addresses
            # if there is a main email address offer that as well (unless it's
            # already there)
            if email is not None and email not in self.email_addresses:
                self.email_addresses[email] = {
                    'email': email,
                    'verified': False,
                    'primary': False,
                }
            choices = []
            verified_emails = []
            for email_data in self.email_addresses.values():
                email_address = email_data['email']
                if email_data['verified']:
                    verified_emails.append(email_address)
                choices.append((email_address, email_address))
            if extra_email_addresses:
                choices.append((form.other_email_value, _('Other:')))
            else:
                choices.append((form.other_email_value, _('Email:')))
            email_select = forms.RadioSelect(choices=choices,
                                             attrs={'id': 'email'})
            form.fields['email'].widget = email_select
            form.initial.update(email=choices[0])
            if not email and len(verified_emails) == 1:
                form.initial.update(email=verified_emails[0])
        return form

    def form_valid(self, form):
        """
        We use the selected email here and reset the social logging list of
        email addresses before they get created.

        We send our welcome email via celery during complete_signup.
        So, we need to manually commit the user to the db for it.
        """
        selected_email = form.cleaned_data['email']
        if form.other_email_used:
            data = {
                'email': selected_email,
                'verified': False,
                'primary': True,
            }
        else:
            data = self.email_addresses.get(selected_email, None)

        if data:
            primary_email_address = EmailAddress(email=data['email'],
                                                 verified=data['verified'],
                                                 primary=True)
            form.sociallogin.email_addresses = \
                self.sociallogin.email_addresses = [primary_email_address]
            if data['verified']:
                # we have to stash the selected email address here
                # so that no email verification is sent again
                # this is done by adding the email address to the session
                get_adapter().stash_verified_email(self.request,
                                                   data['email'])

        with transaction.atomic():
            form.save(self.request)
        return helpers.complete_social_signup(self.request,
                                              self.sociallogin)

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)

        # For GitHub/Google users, find matching legacy Persona social accounts
        assert self.sociallogin.account.provider in ('github', 'google')
        uids = Q()
        for email_address in self.email_addresses.values():
            if email_address['verified']:
                uids |= Q(uid=email_address['email'])
        if uids:
            # only persona accounts have emails as UIDs
            # but adding the provider criteria makes this explicit and future-proof
            matching_accounts = SocialAccount.objects.filter(uids, provider='persona')
        else:
            matching_accounts = SocialAccount.objects.none()

        context.update({
            'default_email': self.default_email,
            'email_addresses': self.email_addresses,
            'matching_user': self.matching_user,
            'matching_accounts': matching_accounts,
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        response = verify_honeypot_value(request, None)
        if isinstance(response, HttpResponseBadRequest):
            return response
        return super(SignupView, self).dispatch(request, *args, **kwargs)


signup = redirect_in_maintenance_mode(SignupView.as_view())


@require_POST
@redirect_in_maintenance_mode
def send_recovery_email(request):
    """
    Send a recovery email to a user.
    """
    form = UserRecoveryEmailForm(data=request.POST)
    if form.is_valid():
        form.save(request=request)
        return redirect('users.recovery_email_sent')
    else:
        return HttpResponseBadRequest('Invalid request.')


@redirect_in_maintenance_mode
def recover(request, uidb64=None, token=None):
    """
    Login via an account recovery link.

    Modeled on django.contrib.auth.views.password_reset_confirm, but resets
    the password to an unusable password instead of prompting for a new
    password.
    """
    UserModel = get_user_model()
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        login(request, user, 'kuma.users.auth_backends.KumaAuthBackend')
        return redirect('users.recover_done')
    return render(request, 'users/recover_failed.html')


recovery_email_sent = TemplateView.as_view(
    template_name='users/recovery_email_sent.html')


recover_done = login_required(never_cache(ConnectionsView.as_view(
    template_name='users/recover_done.html')))

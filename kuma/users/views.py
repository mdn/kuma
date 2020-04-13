import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

import stripe
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.socialaccount import helpers
from allauth.socialaccount.views import ConnectionsView
from allauth.socialaccount.views import SignupView as BaseSignupView
from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import validate_email, ValidationError
from django.db import IntegrityError, transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from honeypot.decorators import verify_honeypot_value
from raven.contrib.django.models import client as raven_client
from waffle import flag_is_active

from kuma.attachments.models import AttachmentRevision
from kuma.core.decorators import (
    ensure_wiki_domain,
    login_required,
    redirect_in_maintenance_mode,
)
from kuma.core.email_utils import render_email
from kuma.core.ga_tracking import (
    ACTION_PROFILE_AUDIT,
    ACTION_PROFILE_EDIT,
    ACTION_PROFILE_EDIT_ERROR,
    ACTION_SUBSCRIPTION_CANCELED,
    ACTION_SUBSCRIPTION_CREATED,
    CATEGORY_MONTHLY_PAYMENTS,
    CATEGORY_SIGNUP_FLOW,
    track_event,
)
from kuma.core.utils import requests_retry_session, send_mail_retrying, urlparams
from kuma.payments.utils import cancel_stripe_customer_subscription
from kuma.wiki.forms import RevisionAkismetSubmissionSpamForm
from kuma.wiki.models import (
    Document,
    DocumentDeletionLog,
    Revision,
    RevisionAkismetSubmission,
)
from kuma.wiki.templatetags.jinja_helpers import absolutify

# we have to import the SignupForm form here due to allauth's odd form subclassing
# that requires providing a base form class (see ACCOUNT_SIGNUP_FORM_CLASS)
from .forms import UserBanForm, UserDeleteForm, UserEditForm, UserRecoveryEmailForm
from .models import User, UserBan, UserSubscription
from .signup import SignupForm
from .stripe_utils import (
    create_stripe_customer_and_subscription_for_user,
    get_stripe_customer,
    get_stripe_subscription_info,
)


@ensure_wiki_domain
@permission_required("users.add_userban")
def ban_user(request, username):
    """
    Ban a user.
    """
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    if request.method == "POST":
        form = UserBanForm(data=request.POST)
        if form.is_valid():
            ban = UserBan(
                user=user,
                by=request.user,
                reason=form.cleaned_data["reason"],
                is_active=True,
            )
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
        common_reasons = ["Spam"]
    else:
        if not common_reasons:
            common_reasons = ["Spam"]
    return render(
        request,
        "users/ban_user.html",
        {"form": form, "detail_user": user, "common_reasons": common_reasons},
    )


@ensure_wiki_domain
@permission_required("users.add_userban")
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
    revisions = user.created_revisions.prefetch_related("document")
    revisions = revisions.defer("content", "summary").order_by("-id")
    revisions = revisions.filter(created__gte=date_three_days_ago)
    revisions_not_spam = revisions.filter(akismet_submissions=None)

    return render(
        request,
        "users/ban_user_and_cleanup.html",
        {
            "detail_user": user,
            "user_banned": user_ban,
            "revisions": revisions,
            "revisions_not_spam": revisions_not_spam,
            "on_ban_page": True,
        },
    )


@ensure_wiki_domain
@require_POST
@permission_required("users.add_userban")
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
        ban = UserBan(user=user, by=request.user, reason="Spam", is_active=True)
        ban.save()
    else:
        user_ban.update(by=request.user, reason="Spam")

    date_three_days_ago = datetime.now().date() - timedelta(days=3)
    revisions_from_last_three_days = user.created_revisions.prefetch_related("document")
    revisions_from_last_three_days = revisions_from_last_three_days.defer(
        "content", "summary"
    ).order_by("-id")
    revisions_from_last_three_days = revisions_from_last_three_days.filter(
        created__gte=date_three_days_ago
    )

    """ The "Actions Taken" section """
    # The revisions to be submitted to Akismet and reverted,
    # these must be sorted descending so that they are reverted accordingly
    revisions_to_mark_as_spam_and_revert = revisions_from_last_three_days.filter(
        id__in=request.POST.getlist("revision-id")
    ).order_by("-id")

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
        rev
        for rev in revision_by_distinct_doc(revisions_to_mark_as_spam_and_revert)
        if rev.document.current_revision != rev
    ]
    previous_good_rev = {}

    for revision in revisions_to_mark_as_spam_and_revert:
        submission = RevisionAkismetSubmission(sender=request.user, type="spam")
        akismet_submission_data = {"revision": revision.id}

        data = RevisionAkismetSubmissionSpamForm(
            data=akismet_submission_data, instance=submission, request=request
        )
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
            revision.document.refresh_from_db(fields=["current_revision"])
        except Document.DoesNotExist:
            continue  # This document was previously deleted in this loop, continue
        if (
            revision.document.current_revision
            not in revisions_to_mark_as_spam_and_revert
        ):
            if revision.document_id not in previous_good_rev:
                previous_good_rev[
                    revision.document_id
                ] = revision.document.current_revision

            continue  # This document has a more current revision, no need to revert

        # Loop through all previous revisions to find the oldest spam
        # revision on a specific document from this request.
        while revision.previous in revisions_to_mark_as_spam_and_revert:
            revision = revision.previous
        # If this is a new revision on an existing document, revert it
        if revision.previous:
            previous_good_rev[revision.document_id] = revision.previous

            reverted = revert_document(
                request=request, revision_id=revision.previous.id
            )
            if reverted:
                revisions_reverted_list.append(revision)
            else:
                # If the revert was unsuccessful, include this in the follow-up list
                revisions_not_reverted_list.append(revision)

        # If this is a new document/translation, delete it
        else:
            deleted = delete_document(request=request, document=revision.document)
            if deleted:
                revisions_deleted_list.append(revision)
            else:
                # If the delete was unsuccessful, include this in the follow-up list
                revisions_not_deleted_list.append(revision)

    # Find just the latest revision for each document
    submitted_to_akismet_by_distinct_doc = revision_by_distinct_doc(
        submitted_to_akismet
    )
    not_submitted_to_akismet_by_distinct_doc = revision_by_distinct_doc(
        not_submitted_to_akismet
    )
    revisions_reverted_by_distinct_doc = revision_by_distinct_doc(
        revisions_reverted_list
    )
    revisions_not_reverted_by_distinct_doc = revision_by_distinct_doc(
        revisions_not_reverted_list
    )
    revisions_deleted_by_distinct_doc = revision_by_distinct_doc(revisions_deleted_list)
    revisions_not_deleted_by_distinct_doc = revision_by_distinct_doc(
        revisions_not_deleted_list
    )

    actions_taken = {
        "revisions_reported_as_spam": submitted_to_akismet_by_distinct_doc,
        "revisions_reverted_list": revisions_reverted_by_distinct_doc,
        "revisions_deleted_list": revisions_deleted_by_distinct_doc,
    }

    """ The "Needs followup" section """
    # TODO: Phase V: If user made actions while reviewer was banning them
    new_action_by_user = []
    skipped_revisions = [
        rev
        for rev in revisions_to_mark_as_spam_and_revert
        if rev.document_id in previous_good_rev
        and rev.id < previous_good_rev[rev.document_id].id
    ]
    skipped_revisions = revision_by_distinct_doc(skipped_revisions)

    needs_follow_up = {
        "manual_revert": new_action_by_user,
        "skipped_revisions": skipped_revisions,
        "not_submitted_to_akismet": not_submitted_to_akismet_by_distinct_doc,
        "not_reverted_list": revisions_not_reverted_by_distinct_doc,
        "not_deleted_list": revisions_not_deleted_by_distinct_doc,
    }

    """ The "No Actions Taken" section """
    revisions_already_spam = revisions_from_last_three_days.filter(
        id__in=request.POST.getlist("revision-already-spam")
    )
    revisions_already_spam = list(revisions_already_spam)
    revisions_already_spam_by_distinct_doc = revision_by_distinct_doc(
        revisions_already_spam
    )

    identified_as_not_spam = [
        rev
        for rev in revisions_from_last_three_days
        if rev not in revisions_already_spam
        and rev not in revisions_to_mark_as_spam_and_revert
    ]
    identified_as_not_spam_by_distinct_doc = revision_by_distinct_doc(
        identified_as_not_spam
    )

    no_actions_taken = {
        "latest_revision_is_not_spam": latest_is_not_spam,
        "revisions_already_identified_as_spam": revisions_already_spam_by_distinct_doc,
        "revisions_identified_as_not_spam": identified_as_not_spam_by_distinct_doc,
    }

    context = {
        "detail_user": user,
        "form": UserBanForm(),
        "actions_taken": actions_taken,
        "needs_follow_up": needs_follow_up,
        "no_actions_taken": no_actions_taken,
    }

    # Send an email to the spam watch mailing list.
    ban_and_revert_notification(user, request.user, context)

    return render(request, "users/ban_user_and_cleanup_summary.html", context)


def revision_by_distinct_doc(list_of_revisions):
    documents = {}
    for rev in list_of_revisions:
        documents.setdefault(rev.document_id, rev)
        if documents[rev.document_id].id < rev.id:
            documents[rev.document_id] = rev

    return [documents[doc_id] for doc_id in sorted(documents)]


def ban_and_revert_notification(spammer, moderator, info):
    subject = "[MDN] %s has been banned by %s" % (spammer, moderator)
    context = {"spammer": spammer, "moderator": moderator}
    context.update(info)
    body = render_to_string("wiki/email/spam_ban.ltxt", context)

    send_mail(
        subject, body, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_LIST_SPAM_WATCH]
    )


@permission_required("users.add_userban")
def revert_document(request, revision_id):
    """
    Revert document to a specific revision.
    """
    revision = get_object_or_404(
        Revision.objects.select_related("document"), pk=revision_id
    )

    comment = "spam"
    document = revision.document
    old_revision_pk = revision.pk
    try:
        new_revision = document.revert(revision, request.user, comment)
        # schedule a rendering of the new revision if it really was saved
        if new_revision.pk != old_revision_pk:  # pragma: no branch
            document.schedule_rendering("max-age=0")
    except IntegrityError:
        return False
    return True


@permission_required("wiki.delete_document")
def delete_document(request, document):
    """
    Delete a Document.
    """
    try:
        DocumentDeletionLog.objects.create(
            locale=document.locale,
            slug=document.slug,
            user=request.user,
            reason="Spam",
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

    if detail_user.active_ban and not request.user.has_perm("users.add_userban"):
        return render(request, "404.html", {"reason": "banneduser"}, status=404)

    context = {"detail_user": detail_user}
    return render(request, "users/user_detail.html", context)


@login_required
def my_detail_page(request):
    return redirect(request.user)


@login_required
def my_edit_page(request):
    return redirect("users.user_edit", request.user.username)


@redirect_in_maintenance_mode
def user_edit(request, username):
    """
    View and edit user profile
    """
    edit_user = get_object_or_404(User, username=username)

    if not edit_user.allows_editing_by(request.user):
        return HttpResponseForbidden()

    revisions = Revision.objects.filter(creator=edit_user)
    attachment_revisions = AttachmentRevision.objects.filter(creator=edit_user)

    if request.method != "POST":
        initial = {
            "beta": edit_user.is_beta_tester,
            "username": edit_user.username,
            "is_github_url_public": edit_user.is_github_url_public,
        }

        # Finally, set up the forms.
        user_form = UserEditForm(instance=edit_user, initial=initial, prefix="user")
    else:
        user_form = UserEditForm(
            data=request.POST, files=request.FILES, instance=edit_user, prefix="user"
        )

        if user_form.is_valid():
            user_form.save()

            try:
                # Beta
                beta_group = Group.objects.get(name=settings.BETA_GROUP_NAME)
                if user_form.cleaned_data["beta"]:
                    beta_group.user_set.add(request.user)
                else:
                    beta_group.user_set.remove(request.user)
            except Group.DoesNotExist:
                # If there's no Beta Testers group, ignore that logic
                pass

            return redirect(edit_user)

    # Needed so the template can know to show a warning message and the
    # template doesn't want to do code logic to look into the 'request' object.
    has_stripe_error = request.GET.get("has_stripe_error", "False") == "True"

    context = {
        "edit_user": edit_user,
        "user_form": user_form,
        "username": user_form["username"].value(),
        "form": UserDeleteForm(username=username),
        "revisions": revisions,
        "attachment_revisions": attachment_revisions,
        "subscription_info": _retrieve_and_synchronize_subscription_info(edit_user),
        "has_stripe_error": has_stripe_error,
        "next_subscriber_number": User.get_highest_subscriber_number() + 1,
    }

    return render(request, "users/user_edit.html", context)


def _retrieve_and_synchronize_subscription_info(user):
    """For the given user, if it has as 'stripe_customer_id' retrieve the info
    about the subscription if it's there. All packaged in a way that is
    practical for the stripe_subscription.html template.

    Also, whilst doing this check, we also verify that the UserSubscription record
    for this user is right. Doing that check is a second-layer check in case
    our webhooks have failed us.
    """
    subscription_info = None
    stripe_customer = get_stripe_customer(user)
    if stripe_customer:
        stripe_subscription_info = get_stripe_subscription_info(stripe_customer)
        if stripe_subscription_info:
            source = stripe_customer.default_source
            if source.object == "card":
                card = source
            elif source.object == "source":
                card = source.card
            else:
                raise ValueError(
                    f"unexpected stripe customer default_source of type {source.object!r}"
                )

            subscription_info = {
                "next_payment_at": datetime.fromtimestamp(
                    stripe_subscription_info.current_period_end
                ),
                "brand": card.brand,
                "expires_at": f"{card.exp_month}/{card.exp_year}",
                "last4": card.last4,
                # Cards that are part of a "source" don't have a zip
                "zip": card.get("address_zip", None),
            }

            # To perfect the synchronization, take this opportunity to make sure
            # we have an up-to-date record of this.
            UserSubscription.set_active(user, stripe_subscription_info.id)
        else:
            # The user has a stripe_customer_id but no active subscription
            # on the current settings.STRIPE_PLAN_ID! Perhaps it has been cancelled
            # and not updated in our own records.
            for user_subscription in UserSubscription.objects.filter(
                user=user, canceled__isnull=True
            ):
                user_subscription.canceled = timezone.now()
                user_subscription.save()

    return subscription_info


@redirect_in_maintenance_mode
@login_required
@transaction.atomic()
def user_delete(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return HttpResponseForbidden()

    def donate_attributions():
        anon, _ = User.objects.get_or_create(username="Anonymous")
        user.created_revisions.update(creator=anon)
        user.created_attachment_revisions.update(creator=anon)

    def scrub_user():
        # Before doing anything, cancel any active subscriptions first.
        if user.stripe_customer_id:
            for subscription in cancel_stripe_customer_subscription(
                user.stripe_customer_id
            ):
                UserSubscription.set_canceled(request.user, subscription.id)

        # From the User abstract class
        user.first_name = ""
        user.last_name = ""
        user.email = ""

        # All User attributes
        user.timezone = ""
        user.locale = ""
        user.homepage = ""
        user.title = ""
        user.fullname = ""
        user.organization = ""
        user.location = ""
        user.bio = ""
        user.irc_nickname = ""
        user.website_url = ""
        user.github_url = ""
        user.mozillians_url = ""
        user.twitter_url = ""
        user.linkedin_url = ""
        user.facebook_url = ""
        user.stackoverflow_url = ""
        user.discourse_url = ""
        user.stripe_customer_id = ""
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
        anon, _ = User.objects.get_or_create(username="Anonymous")
        user.revisionakismetsubmission_set.update(sender=anon)
        user.documentdeletionlog_set.update(user=anon)
        user.documentspamattempt_set.update(user=anon)
        user.documentspam_reviewed.update(reviewer=anon)
        user.bans.update(user=anon)
        user.bans_issued.update(by=anon)

        user.delete()

    revisions = Revision.objects.filter(creator=request.user)
    attachment_revisions = AttachmentRevision.objects.filter(creator=request.user)
    context = {}
    if request.method == "POST":
        # If the user has no revisions there's not choices on the form.
        if revisions.exists() or attachment_revisions.exists():
            form = UserDeleteForm(request.POST, username=username)
            if form.is_valid():
                if form.cleaned_data["attributions"] == "donate":
                    donate_attributions()
                    delete_user()
                elif form.cleaned_data["attributions"] == "keep":
                    scrub_user()
                    force_logout()
                else:
                    raise NotImplementedError(form.cleaned_data["attributions"])
                return HttpResponseRedirect("/")

        else:
            delete_user()
            return HttpResponseRedirect("/")
    else:
        form = UserDeleteForm(username=username)

    context["form"] = form
    context["username"] = username
    context["revisions"] = revisions
    context["attachment_revisions"] = attachment_revisions

    return render(request, "users/user_delete.html", context)


def signin_landing(request):
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
        form.fields["email"].label = _("Email address")

        # We should only see GitHub/Google users.
        assert self.sociallogin.account.provider in ("github", "google")

        initial_username = form.initial.get("username") or ""

        # When no username is provided, try to derive one from the email address.
        if not initial_username:
            email = form.initial.get("email")
            if email:
                if isinstance(email, tuple):
                    email = email[0]
                initial_username = email.split("@")[0]

        if initial_username:
            # Find a new username if it clashes with an existing username.
            increment = 1
            User = get_user_model()
            initial_username_base = initial_username
            while User.objects.filter(username__iexact=initial_username).exists():
                increment += 1
                initial_username = f"{initial_username_base}{increment}"

        form.initial["username"] = initial_username

        email = self.sociallogin.account.extra_data.get("email") or None
        email_data = self.sociallogin.account.extra_data.get("email_addresses") or []

        # Discard email addresses that won't validate
        extra_email_addresses = []
        for data in email_data:
            try:
                validate_email(data["email"])
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
                self.email_addresses[email_address["email"]] = email_address

            # build the choice list with the given email addresses
            # if there is a main email address offer that as well (unless it's
            # already there)
            if email is not None and email not in self.email_addresses:
                self.email_addresses[email] = {
                    "email": email,
                    "verified": False,
                    "primary": False,
                }
        return form

    def form_valid(self, form):
        """
        We use the selected email here and reset the social logging list of
        email addresses before they get created.

        We send our welcome email via celery during complete_signup.
        So, we need to manually commit the user to the db for it.
        """

        selected_email = form.cleaned_data["email"]
        if selected_email in self.email_addresses:
            data = self.email_addresses[selected_email]
        elif selected_email == self.default_email:
            data = {
                "email": selected_email,
                "verified": True,
                "primary": True,
            }
        else:
            return HttpResponseBadRequest("email not a valid choice")

        primary_email_address = EmailAddress(
            email=data["email"], verified=data["verified"], primary=True
        )
        form.sociallogin.email_addresses = self.sociallogin.email_addresses = [
            primary_email_address
        ]
        if data["verified"]:
            # we have to stash the selected email address here
            # so that no email verification is sent again
            # this is done by adding the email address to the session
            get_adapter().stash_verified_email(self.request, data["email"])

        with transaction.atomic():
            saved_user = form.save(self.request)

            if saved_user.username != form.initial["username"]:
                track_event(
                    CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_EDIT, "username edit",
                )

        return helpers.complete_social_signup(self.request, self.sociallogin)

    def form_invalid(self, form):
        """
        This is called on POST but only when the form is invalid. We're
        overriding this method simply to send GA events when we find an
        error in the username field.
        """
        if form.errors.get("username") is not None:
            track_event(
                CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_EDIT_ERROR, "username",
            )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        context.update(
            {
                "default_email": self.default_email,
                "email_addresses": self.email_addresses,
            }
        )
        return context

    def dispatch(self, request, *args, **kwargs):
        response = verify_honeypot_value(request, None)
        if isinstance(response, HttpResponseBadRequest):
            return response
        return super(SignupView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """This exists so we can squeeze in a tracking event exclusively
        about viewing the profile creation page. If we did it to all
        dispatch() it would trigger on things like submitting form, which
        might trigger repeatedly if the form submission has validation
        errors that the user has to address.
        """
        if request.session.get("sociallogin_provider"):
            track_event(
                CATEGORY_SIGNUP_FLOW,
                ACTION_PROFILE_AUDIT,
                request.session["sociallogin_provider"],
            )
        return super().get(request, *args, **kwargs)


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
        return redirect("users.recovery_email_sent")
    else:
        return HttpResponseBadRequest("Invalid request.")


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
        login(request, user, "kuma.users.auth_backends.KumaAuthBackend")
        return redirect("users.recover_done")
    return render(request, "users/recover_failed.html")


@login_required
@require_POST
def create_stripe_subscription(request):
    user = request.user

    if not flag_is_active(request, "subscription"):
        return HttpResponseForbidden("subscription flag not active for this user")

    has_stripe_error = False
    try:
        email = request.POST.get("stripe_email", "")
        stripe_token = request.POST.get("stripe_token", "")
        create_stripe_customer_and_subscription_for_user(user, email, stripe_token)

    except stripe.error.StripeError:
        raven_client.captureException()
        has_stripe_error = True

    return redirect(
        urlparams(
            reverse("users.user_edit", args=[user.username]),
            has_stripe_error=has_stripe_error,
        )
        + "#subscription"
    )


recovery_email_sent = TemplateView.as_view(
    template_name="users/recovery_email_sent.html"
)


recover_done = login_required(
    never_cache(ConnectionsView.as_view(template_name="users/recover_done.html"))
)


@csrf_exempt
def stripe_hooks(request):
    try:
        payload = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest("Invalid JSON payload")

    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
    except stripe.error.StripeError:
        raven_client.captureException()
        return HttpResponseBadRequest()

    # Generally, for this list of if-statements, see the create_missing_stripe_webhook
    # function.
    # The list of events there ought to at least minimally match what we're prepared
    # to deal with here.

    if event.type == "invoice.payment_succeeded":
        payment_intent = event.data.object
        _send_payment_received_email(
            payment_intent, request.LANGUAGE_CODE,
        )
        track_event(
            CATEGORY_MONTHLY_PAYMENTS,
            ACTION_SUBSCRIPTION_CREATED,
            f"{settings.CONTRIBUTION_AMOUNT_USD:.2f}",
        )

    elif event.type == "customer.subscription.deleted":
        obj = event.data.object
        for user in User.objects.filter(stripe_customer_id=obj.customer):
            UserSubscription.set_canceled(user, obj.id)
        track_event(CATEGORY_MONTHLY_PAYMENTS, ACTION_SUBSCRIPTION_CANCELED, "webhook")

    else:
        return HttpResponseBadRequest(
            f"We did not expect a Stripe webhook of type {event.type!r}"
        )

    return HttpResponse()


def _send_payment_received_email(payment_intent, locale):
    user = get_user_model().objects.get(stripe_customer_id=payment_intent.customer)
    subscription_info = _retrieve_and_synchronize_subscription_info(user)
    locale = locale or settings.WIKI_DEFAULT_LANGUAGE
    context = {
        "payment_date": datetime.fromtimestamp(payment_intent.created),
        "next_payment_date": subscription_info["next_payment_at"],
        "invoice_number": payment_intent.number,
        "cost": settings.CONTRIBUTION_AMOUNT_USD,
        "credit_card_brand": subscription_info["brand"],
        "manage_subscription_url": absolutify(reverse("recurring_payment_management")),
        "faq_url": absolutify(reverse("payments_index")),
        "contact_email": settings.CONTRIBUTION_SUPPORT_EMAIL,
    }
    with translation.override(locale):
        subject = render_email("users/email/payment_received/subject.ltxt", context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        plain = render_email("users/email/payment_received/plain.ltxt", context)

        send_mail_retrying(
            subject,
            plain,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            attachment={
                "name": os.path.basename(urlparse(payment_intent.invoice_pdf).path),
                "bytes": _download_from_url(payment_intent.invoice_pdf),
                "mime": "application/pdf",
            },
        )


def _download_from_url(url):
    pdf_download = requests_retry_session().get(url)
    pdf_download.raise_for_status()
    return pdf_download.content

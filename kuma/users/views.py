import json
from urllib.parse import urlencode, urlparse

from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.socialaccount import helpers
from allauth.socialaccount.views import SignupView as BaseSignupView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import validate_email, ValidationError
from django.db import transaction
from django.http import (
    HttpResponseBadRequest,
    JsonResponse,
)
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


from kuma.core.decorators import redirect_in_maintenance_mode
from kuma.core.ga_tracking import (
    ACTION_PROFILE_AUDIT,
    ACTION_PROFILE_EDIT,
    ACTION_PROFILE_EDIT_ERROR,
    CATEGORY_SIGNUP_FLOW,
    track_event,
)

from .signup import SignupForm


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

        if not email and extra_email_addresses:
            # Pick the first primary email.
            for data in extra_email_addresses:
                if data["primary"]:
                    email = data["email"]
                    break
            else:
                # Pick the first non-primary email.
                email = extra_email_addresses[0]["email"]

        form.initial["email"] = email

        form.data = form.data.copy()
        for key in form.initial:
            if key not in form.data and form.initial[key]:
                form.data[key] = form.initial[key]

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
                    CATEGORY_SIGNUP_FLOW,
                    ACTION_PROFILE_EDIT,
                    "username edit",
                )

        # This won't be needed once this view is entirely catering to Yari.
        self.request.session.pop("yari_signup", None)

        return helpers.complete_social_signup(self.request, self.sociallogin)

    def form_invalid(self, form):
        """
        This is called on POST but only when the form is invalid. We're
        overriding this method simply to send GA events when we find an
        error in the username field.
        """
        if form.errors.get("username") is not None:
            track_event(
                CATEGORY_SIGNUP_FLOW,
                ACTION_PROFILE_EDIT_ERROR,
                "username",
            )
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

        # return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        context.update(
            {
                "default_email": self.default_email,
                "email_addresses": self.email_addresses,
            }
        )
        return context

    def get_next_url_prefix(self, request):
        prefix = ""
        next_url = request.session.get("sociallogin_next_url")
        if next_url and "://" in next_url:
            # If this is local development and the URL is absolute, use that.
            parsed = urlparse(next_url)
            prefix = f"{parsed.scheme}://{parsed.netloc}"
        return prefix

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

        next_url = request.session.get("sociallogin_next_url")
        next_url_prefix = self.get_next_url_prefix(request)

        socialaccount_sociallogin = request.session.get("socialaccount_sociallogin")
        if not socialaccount_sociallogin:
            # This means first used Yari to attempt to sign in but arrived
            # ignored the outcomes and manually went to the Kuma signup URL.
            # We have to kick you out and ask you to start over. But where to?
            yari_signin_url = (
                f"{next_url_prefix}/{request.LANGUAGE_CODE}{settings.LOGIN_URL}"
            )
            return redirect(yari_signin_url)

        # Things that are NOT PII.
        safe_user_details = {}
        account = socialaccount_sociallogin["account"]
        extra_data = account["extra_data"]
        if extra_data.get("name"):
            safe_user_details["name"] = extra_data["name"]
        if extra_data.get("picture"):  # Google OAuth2
            safe_user_details["avatar_url"] = extra_data["picture"]
        elif extra_data.get("avatar_url"):  # GitHub OAuth2
            safe_user_details["avatar_url"] = extra_data["avatar_url"]
        params = {
            "next": next_url,
            "user_details": json.dumps(safe_user_details),
            "csrfmiddlewaretoken": get_token(request),
            "provider": account.get("provider"),
        }
        yari_signup_url = f"{next_url_prefix}/{request.LANGUAGE_CODE}/signup"
        return redirect(yari_signup_url + "?" + urlencode(params))


signup = redirect_in_maintenance_mode(SignupView.as_view())

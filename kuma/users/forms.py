from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from sundial.forms import TimezoneChoiceField
from sundial.zones import COMMON_GROUPED_CHOICES


from .constants import USERNAME_CHARACTERS, USERNAME_LEGACY_REGEX, USERNAME_REGEX
from .models import User
from .tasks import send_recovery_email


class UserBanForm(forms.Form):
    """
    The form used in the view that enables admins to ban users.
    """

    reason = forms.CharField(widget=forms.Textarea)


class UserEditForm(forms.ModelForm):
    """
    The main form to edit user profile data.

    It dynamically adds a bunch of fields for maintaining information
    about a user's websites
    """

    timezone = TimezoneChoiceField(
        label=_("Timezone"),
        initial=settings.TIME_ZONE,
        choices=COMMON_GROUPED_CHOICES,
        required=False,
    )
    beta = forms.BooleanField(label=_("Beta tester"), required=False,)
    username = forms.RegexField(
        label=_("Username"),
        regex=USERNAME_REGEX,
        max_length=30,
        required=False,
        error_messages={"invalid": USERNAME_CHARACTERS},
    )
    twitter_url = forms.CharField(
        label=_("Twitter"),
        required=False,
        validators=[User.WEBSITE_VALIDATORS["twitter"]],
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://twitter.com/",
                "data-fa-icon": "icon-twitter",
            }
        ),
    )
    github_url = forms.CharField(
        label=_("GitHub"),
        required=False,
        validators=[User.WEBSITE_VALIDATORS["github"]],
        widget=forms.TextInput(
            attrs={"placeholder": "https://github.com/", "data-fa-icon": "icon-github"}
        ),
    )
    is_github_url_public = forms.BooleanField(
        label=_("Display a link to GitHub on my profile"), required=False
    )
    stackoverflow_url = forms.CharField(
        label=_("Stack Overflow"),
        required=False,
        validators=[User.WEBSITE_VALIDATORS["stackoverflow"]],
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://stackoverflow.com/users/",
                "data-fa-icon": "icon-stackexchange",
            }
        ),
    )
    linkedin_url = forms.CharField(
        label=_("LinkedIn"),
        required=False,
        validators=[User.WEBSITE_VALIDATORS["linkedin"]],
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://www.linkedin.com/",
                "data-fa-icon": "icon-linkedin",
            }
        ),
    )
    mozillians_url = forms.CharField(
        label=_("Mozillians"),
        required=False,
        validators=[User.WEBSITE_VALIDATORS["mozillians"]],
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://mozillians.org/u/",
                "data-fa-icon": "icon-group",
            }
        ),
    )
    facebook_url = forms.CharField(
        label=_("Facebook"),
        required=False,
        validators=[User.WEBSITE_VALIDATORS["facebook"]],
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://www.facebook.com/",
                "data-fa-icon": "icon-facebook",
            }
        ),
    )
    discourse_url = forms.CharField(
        label=_("Discourse"),
        required=False,
        validators=[User.WEBSITE_VALIDATORS["discourse"]],
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://discourse.mozilla.org/u/",
                "data-fa-icon": "icon-discourse",
            }
        ),
    )
    is_newsletter_subscribed = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = (
            "fullname",
            "title",
            "organization",
            "location",
            "locale",
            "timezone",
            "irc_nickname",
            "twitter_url",
            "github_url",
            "is_github_url_public",
            "stackoverflow_url",
            "linkedin_url",
            "mozillians_url",
            "facebook_url",
            "discourse_url",
            "username",
            "is_newsletter_subscribed"
        )

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        # in case the username is not changed and the user has a legacy
        # username we want to disarm the username regex
        if (
            "username" not in self.changed_data
            and self.instance
            and self.instance.has_legacy_username
        ):
            self.fields["username"].regex = USERNAME_LEGACY_REGEX

    def clean_username(self):
        new_username = self.cleaned_data["username"]

        if not new_username:
            raise forms.ValidationError(_("This field cannot be blank."))

        if (
            self.instance is not None
            and User.objects.exclude(pk=self.instance.pk)
            .filter(username=new_username)
            .exists()
        ):
            raise forms.ValidationError(_("Username already in use."))
        return new_username


class UserRecoveryEmailForm(forms.Form):
    """
    Send email(s) with an account recovery link.

    Modeled after django.contrib.auth.forms.PasswordResetForm
    """

    email = forms.EmailField(label=_("Email"), max_length=254)

    def save(self, request):
        """
        Send email(s) with an account recovery link.
        """
        email = self.cleaned_data["email"]

        # Gather matching active users
        active_users = User.objects.filter(is_active=True)
        # Users using email as the primary contact email
        primary_users = active_users.filter(email__iexact=email)
        # Users with a matching Persona account
        personas = active_users.filter(
            socialaccount__uid__iexact=email, socialaccount__provider="persona"
        )
        # Users with that confirmed email
        confirmed = active_users.filter(emailaddress__email__iexact=email)

        # Send one account recovery email to each matching user
        user_pks = set()
        user_pks.update(primary_users.values_list("pk", flat=True))
        user_pks.update(personas.values_list("pk", flat=True))
        user_pks.update(confirmed.values_list("pk", flat=True))
        for user_pk in sorted(user_pks):
            # TODO figure out why this isn't a .delay() call.
            # https://bugzilla.mozilla.org/show_bug.cgi?id=1544925
            send_recovery_email(user_pk, email, request.LANGUAGE_CODE)


class UserDeleteForm(forms.Form):
    def __init__(self, *args, username, **kwargs):
        super().__init__(*args, **kwargs)

        choices = {
            "keep": (
                _("Keep my attribution for my page changes (%(username)s)")
                % {"username": username}
            ),
            "donate": _('Switch my attribution for my page changes to "Anonymous"'),
        }

        self.fields["attributions"].choices = choices.items()

    attributions = forms.ChoiceField(required=True, widget=forms.widgets.RadioSelect())

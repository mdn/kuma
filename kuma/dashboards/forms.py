from django import forms
from django.conf import settings
from django.forms.fields import CharField
from django.utils.translation import ugettext_lazy as _


LANG_CHOICES = [("", _("All Locales"))] + settings.SORTED_LANGUAGES
PERIOD_CHOICES = [
    ("", _("None")),
    ("hour", _("Hour")),
    ("day", _("Day")),
    ("week", _("Week")),
    ("month", _("30 days")),
]


class RevisionDashboardForm(forms.Form):
    ALL_AUTHORS = 0
    KNOWN_AUTHORS = 1
    UNKNOWN_AUTHORS = 2
    AUTHOR_CHOICES = [
        (ALL_AUTHORS, _("All Authors")),
        (KNOWN_AUTHORS, _("Known Authors")),
        (UNKNOWN_AUTHORS, _("Unknown Authors")),
    ]

    locale = forms.ChoiceField(
        choices=LANG_CHOICES,
        # Required for non-translations, which is
        # enforced in Document.clean().
        required=False,
        label=_("Locale:"),
    )
    user = CharField(min_length=1, max_length=255, required=False, label=_("User:"))
    topic = CharField(min_length=1, max_length=255, required=False, label=_("Topic:"))
    start_date = forms.DateField(
        required=False,
        label=_("Start Date:"),
        input_formats=["%m/%d/%Y"],
        widget=forms.TextInput(attrs={"pattern": r"\d{1,2}/\d{1,2}/\d{4}"}),
    )
    end_date = forms.DateField(
        required=False,
        label=_("End Date:"),
        input_formats=["%m/%d/%Y"],
        widget=forms.TextInput(attrs={"pattern": r"\d{1,2}/\d{1,2}/\d{4}"}),
    )
    preceding_period = forms.ChoiceField(
        choices=PERIOD_CHOICES, required=False, label=_("Preceding Period:")
    )
    authors = forms.ChoiceField(
        choices=AUTHOR_CHOICES, required=False, label=_("Authors")
    )

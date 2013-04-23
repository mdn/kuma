import time

from django import forms
from django.conf import settings
from django.forms.util import ValidationError

from tower import ugettext_lazy as _lazy

import search as constants
from sumo.form_fields import TypedMultipleChoiceField
from sumo_locales import LOCALES
from wiki.models import CATEGORIES, FIREFOX_VERSIONS, OPERATING_SYSTEMS


SEARCH_LANGUAGES = [(k, LOCALES[k].native) for
                    k in settings.SUMO_LANGUAGES]


class SearchForm(forms.Form):
    """Django form for handling display and validation"""

    def clean(self):
        """Clean up data and set defaults"""
        c = self.cleaned_data

        if ('a' not in c or not c['a']) and c['q'] == '':
            raise ValidationError('Basic search requires a query string.')

        # Validate created and updated dates
        date_fields = (('updated', 'updated_date'),
                        #('created', 'created_date'),
                        )
        for field_option, field_date in date_fields:
            if c[field_date] != '':
                try:
                    created_timestamp = time.mktime(
                        time.strptime(c[field_date], '%m/%d/%Y'))
                    c[field_date] = int(created_timestamp)
                except (ValueError, OverflowError):
                    c[field_option] = None
            else:
                c[field_option] = None

        # Empty value defaults to int
        c['num_votes'] = c.get('num_votes') or 0
        return c

    # Common fields
    q = forms.CharField(required=False)

    w = forms.TypedChoiceField(required=False, coerce=int,
                               widget=forms.HiddenInput,
                               empty_value=constants.WHERE_BASIC,
                               choices=((constants.WHERE_SUPPORT, None),
                                        (constants.WHERE_WIKI, None),
                                        (constants.WHERE_BASIC, None),
                                        (constants.WHERE_DISCUSSION, None)))

    a = forms.IntegerField(required=False, widget=forms.HiddenInput)

    # KB fields
    tag_widget = forms.TextInput(attrs={'placeholder': _lazy('tag1, tag2'),
                                        'class': 'auto-fill'})
    tags = forms.CharField(required=False, widget=tag_widget,
                           label=_lazy('Tags'))

    language = forms.ChoiceField(required=False, label=_lazy('Language'),
                                 choices=SEARCH_LANGUAGES)

    category = TypedMultipleChoiceField(
        required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
        label=_lazy('Category'), choices=CATEGORIES, coerce_only=True)

    fx = TypedMultipleChoiceField(
        required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
        label=_lazy('Firefox version'),
        choices=[(v.id, v.long) for v in FIREFOX_VERSIONS],
        initial=[v.id for v in FIREFOX_VERSIONS],
        coerce_only=True)

    os = TypedMultipleChoiceField(
        required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
        label=_lazy('Operating System'),
        choices=[(o.id, o.name) for o in OPERATING_SYSTEMS],
        initial=[o.id for o in OPERATING_SYSTEMS],
        coerce_only=True)

    """
    # Support questions and discussion forums fields
    created = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy('Created'), choices=constants.DATE_LIST)

    created_date = forms.CharField(required=False)
    """

    updated = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy('Last updated'), choices=constants.DATE_LIST)
    updated_date = forms.CharField(required=False)

    """
    user_widget = forms.TextInput(attrs={'placeholder': _lazy('username'),
                                         'class': 'auto-fill'})
    # Discussion forums fields
    author = forms.CharField(required=False, widget=user_widget)
    """

    sortby = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy('Sort results by'), choices=constants.SORTBY_FORUMS)

    """
    thread_type = TypedMultipleChoiceField(
        required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
        label=_lazy('Thread type'), choices=constants.DISCUSSION_STATUS_LIST,
        coerce_only=True)

    # Support questions fields
    asked_by = forms.CharField(required=False, widget=user_widget)
    answered_by = forms.CharField(required=False, widget=user_widget)

    sortby_questions = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy('Sort results by'), choices=constants.SORTBY_QUESTIONS)

    is_locked = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy('Locked'), choices=constants.TERNARY_LIST)

    is_solved = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy('Solved'), choices=constants.TERNARY_LIST)

    has_answers = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy('Has answers'), choices=constants.TERNARY_LIST)

    has_helpful = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy('Has helpful answers'), choices=constants.TERNARY_LIST)

    num_voted = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy('Votes'), choices=constants.NUMBER_LIST)
    num_votes = forms.IntegerField(required=False)

    q_tags = forms.CharField(label=_lazy('Tags'), required=False,
                             widget=tag_widget)
    """

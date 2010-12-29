import time

from django import forms
from django.conf import settings
from django.forms.util import ValidationError

from tower import ugettext_lazy as _lazy

from forums.models import Forum as DiscussionForum
import search as constants
from sumo.form_fields import NoValidateMultipleChoiceField
from sumo_locales import LOCALES
from wiki.models import CATEGORIES, FIREFOX_VERSIONS, OPERATING_SYSTEMS


# Form must be nested inside request for fixtures to be used properly
# TODO: If you move it, change _() to _lazy().
class SearchForm(forms.Form):
    """Django form for handling display and validation"""

    def clean(self):
        """Clean up data and set defaults"""

        cleaned_data = self.cleaned_data

        if ('a' not in cleaned_data or
            not cleaned_data['a']) and cleaned_data['q'] == '':
            raise ValidationError('Basic search requires a query string.')

        # Validate created and updated dates
        date_fields = (('created', 'created_date'),
                       ('updated', 'updated_date'))
        for field_option, field_date in date_fields:
            if cleaned_data[field_date] != '':
                try:
                    created_timestamp = time.mktime(
                        time.strptime(cleaned_data[field_date],
                                      '%m/%d/%Y'))
                    cleaned_data[field_date] = int(created_timestamp)
                except (ValueError, OverflowError):
                    cleaned_data[field_option] = None
            else:
                cleaned_data[field_option] = None

        # Validate all integer fields
        if not cleaned_data.get('num_votes'):
            cleaned_data['num_votes'] = 0

        # Set defaults for MultipleChoiceFields and convert to ints.
        # Ticket #12398 adds TypedMultipleChoiceField which would replace
        # MultipleChoiceField + map(int, ...) and use coerce instead.
        if cleaned_data.get('category'):
            try:
                cleaned_data['category'] = map(int,
                                               cleaned_data['category'])
            except ValueError:
                cleaned_data['category'] = None

        try:
            cleaned_data['fx'] = map(int, cleaned_data['fx'])
        except ValueError:
            cleaned_data['fx'] = None

        try:
            cleaned_data['os'] = map(int, cleaned_data['os'])
        except ValueError:
            cleaned_data['os'] = None

        try:
            cleaned_data['forum'] = map(int, cleaned_data.get('forum'))
        except ValueError:
            cleaned_data['forum'] = None

        try:
            cleaned_data['thread_type'] = map(
                int, cleaned_data.get('thread_type'))
        except ValueError:
            cleaned_data['thread_type'] = None

        return cleaned_data

    # Common fields
    q = forms.CharField(required=False)

    w = forms.TypedChoiceField(
        widget=forms.HiddenInput, required=False, coerce=int,
        empty_value=constants.WHERE_BASIC,
        choices=((constants.WHERE_SUPPORT, None),
                 (constants.WHERE_WIKI, None),
                 (constants.WHERE_BASIC, None),
                 (constants.WHERE_DISCUSSION, None)))

    a = forms.IntegerField(widget=forms.HiddenInput, required=False)

    # KB fields
    tag_widget = forms.TextInput(attrs={'placeholder': _lazy('tag1, tag2'),
                                        'class': 'auto-fill'})
    tags = forms.CharField(label=_lazy('Tags'), required=False,
                           widget=tag_widget)

    language = forms.ChoiceField(
        label=_lazy('Language'), required=False,
        choices=[(LOCALES[k].external, LOCALES[k].native) for
                 k in settings.SUMO_LANGUAGES])

    category = NoValidateMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label=_lazy('Category'), choices=CATEGORIES, required=False)

    fx = NoValidateMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label=_lazy('Firefox version'),
        choices=[(v.id, v.long) for v in FIREFOX_VERSIONS],
        initial=[v.id for v in FIREFOX_VERSIONS])

    os = NoValidateMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label=_lazy('Operating System'),
        choices=[(o.id, o.name) for o in OPERATING_SYSTEMS],
        initial=[o.id for o in OPERATING_SYSTEMS])

    # Support questions and discussion forums fields
    created = forms.TypedChoiceField(
        label=_lazy('Created'), coerce=int, empty_value=0,
        choices=constants.DATE_LIST, required=False)
    created_date = forms.CharField(required=False)

    updated = forms.TypedChoiceField(
        label=_lazy('Last updated'), coerce=int, empty_value=0,
        choices=constants.DATE_LIST, required=False)
    updated_date = forms.CharField(required=False)

    user_widget = forms.TextInput(attrs={'placeholder': _lazy('username'),
                                         'class': 'auto-fill'})

    # Discussion forums fields
    author = forms.CharField(required=False, widget=user_widget)

    sortby = forms.TypedChoiceField(
        label=_lazy('Sort results by'), coerce=int, empty_value=0,
        choices=constants.SORTBY_FORUMS, required=False)

    thread_type = NoValidateMultipleChoiceField(
        label=_lazy('Thread type'), choices=constants.DISCUSSION_STATUS_LIST,
        required=False,
        widget=forms.CheckboxSelectMultiple)

    forums = [(f.id, f.name) for f in DiscussionForum.objects.all()]
    forum = NoValidateMultipleChoiceField(label=_lazy('Search in forum'),
                                          choices=forums, required=False)

    # Support questions fields
    asked_by = forms.CharField(required=False, widget=user_widget)
    answered_by = forms.CharField(required=False, widget=user_widget)

    sortby_questions = forms.TypedChoiceField(
        label=_lazy('Sort results by'), coerce=int, empty_value=0,
        choices=constants.SORTBY_QUESTIONS, required=False)

    is_locked = forms.TypedChoiceField(
        label=_lazy('Locked'), coerce=int, empty_value=0,
        choices=constants.TERNARY_LIST, required=False,
        widget=forms.RadioSelect)

    is_solved = forms.TypedChoiceField(
        label=_lazy('Solved'), coerce=int, empty_value=0,
        choices=constants.TERNARY_LIST, required=False,
        widget=forms.RadioSelect)

    has_answers = forms.TypedChoiceField(
        label=_lazy('Has answers'), coerce=int, empty_value=0,
        choices=constants.TERNARY_LIST, required=False,
        widget=forms.RadioSelect)

    has_helpful = forms.TypedChoiceField(
        label=_lazy('Has helpful answers'), coerce=int, empty_value=0,
        choices=constants.TERNARY_LIST, required=False,
        widget=forms.RadioSelect)

    num_voted = forms.TypedChoiceField(
        label=_lazy('Votes'), coerce=int, empty_value=0,
        choices=constants.NUMBER_LIST, required=False)
    num_votes = forms.IntegerField(required=False)

    q_tags = forms.CharField(label=_lazy('Tags'), required=False,
                             widget=tag_widget)

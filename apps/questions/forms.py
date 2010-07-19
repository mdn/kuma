from django import forms

from tower import ugettext_lazy as _lazy

from sumo.form_fields import StrippedCharField
from .models import Answer

# labels and help text
SITE_AFFECTED_LABEL = _lazy(u'URL of affected site')
CRASH_ID_LABEL = _lazy(u'Crash ID(s)')
CRASH_ID_HELP = _lazy(u"If you submit information to Mozilla when you crash, you'll be given a crash ID which uniquely identifies your crash and lets us look at details that may help identify the cause. To find your recently submitted crash IDs, go to <strong>about:crashes</strong> in your location bar. <a href='http://support.mozilla.com/en-US/kb/Firefox+crashes#Getting_the_most_accurate_help_with_your_Firefox_crash' target='_blank'>Click for detailed instructions</a>.")
TROUBLESHOOTING_LABEL = _lazy(u'Troubleshooting Information')
TROUBLESHOOTING_HELP = _lazy(u'Copy and paste the information from <strong>Help &gt; Troubleshooting Information</strong>.')
FREQUENCY_LABEL = _lazy(u'This happened')
FREQUENCY_CHOICES = [(u'', u''),
                     (u'NOT_SURE', _lazy(u'Not sure how often')),
                     (u'ONCE_OR_TWICE', _lazy(u'Just once or twice')),
                     (u'FEW_TIMES_WEEK', _lazy(u'A few times a week')),
                     (u'EVERY_TIME', _lazy(u'Every time Firefox opened')), ]
STARTED_LABEL = _lazy(u'This started when...')
TITLE_LABEL = _lazy(u'Question')
CONTENT_LABEL = _lazy(u'Details')
CONTENT_HELP = _lazy(u'The more information you can provide the better chance your question will be answered.')
EMAIL_LABEL = _lazy(u'Email')
EMAIL_HELP = _lazy(u'A confirmation email will be sent to this address in order to post your question.')
FF_VERSION_LABEL = _lazy(u'Firefox version')
OS_LABEL = _lazy(u'Operating system')
PLUGINS_LABEL = _lazy(u'Installed plugins')
ADDON_LABEL = _lazy(u'Extension/plugin you are having trouble with')

# Validation error messages
MSG_TITLE_REQUIRED = _lazy(u'Please provide a question.')
MSG_TITLE_SHORT = _lazy(u'Your question is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
MSG_TITLE_LONG = _lazy(u'Please keep the length of your question to %(limit_value)s characters or less. It is currently %(show_value)s characters.')
MSG_CONTENT_REQUIRED = _lazy(u'Please provide content.')
MSG_CONTENT_SHORT = _lazy(u'Your content is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
MSG_CONTENT_LONG = _lazy(u'Please keep the length of your content to %(limit_value)s characters or less. It is currently %(show_value)s characters.')


class EditQuestionForm(forms.Form):
    """Form to edit an existing question"""

    def __init__(self, user=None, product=None, category=None, *args,
                 **kwargs):
        """Init the form.

        We are adding fields here and not declaratively because the
        form fields to include depend on the selected product/category.
        """
        super(EditQuestionForm, self).__init__(*args, **kwargs)

        #  Extra fields required by product/category selected
        extra_fields = []

        if product:
            extra_fields += product.get('extra_fields', [])
        if category:
            extra_fields += category.get('extra_fields', [])

        #  Add the fields to the form
        error_messages = {'required': MSG_TITLE_REQUIRED,
                          'min_length': MSG_TITLE_SHORT,
                          'max_length': MSG_TITLE_LONG}
        field = StrippedCharField(label=TITLE_LABEL, min_length=5,
                                  max_length=255, widget=forms.TextInput(),
                                  error_messages=error_messages)
        self.fields['title'] = field

        error_messages = {'required': MSG_CONTENT_REQUIRED,
                          'min_length': MSG_CONTENT_SHORT,
                          'max_length': MSG_CONTENT_LONG}
        field = StrippedCharField(label=CONTENT_LABEL, help_text=CONTENT_HELP,
                                  min_length=5, max_length=10000,
                                  widget=forms.Textarea(),
                                  error_messages=error_messages)
        self.fields['content'] = field

        if 'sites_affected' in extra_fields:
            field = StrippedCharField(label=SITE_AFFECTED_LABEL,
                                      initial='http://',
                                      required=False,
                                      max_length=255,
                                      widget=forms.TextInput())
            self.fields['sites_affected'] = field

        if 'crash_id' in extra_fields:
            field = StrippedCharField(label=CRASH_ID_LABEL,
                                      help_text=CRASH_ID_HELP,
                                      required=False,
                                      max_length=255,
                                      widget=forms.TextInput())
            self.fields['crash_id'] = field

        if 'frequency' in extra_fields:
            field = forms.ChoiceField(label=FREQUENCY_LABEL,
                                      choices=FREQUENCY_CHOICES,
                                      required=False)
            self.fields['frequency'] = field

        if 'started' in extra_fields:
            field = StrippedCharField(label=STARTED_LABEL,
                                      required=False,
                                      max_length=255,
                                      widget=forms.TextInput())
            self.fields['started'] = field

        if 'addon' in extra_fields:
            field = StrippedCharField(label=ADDON_LABEL,
                                      required=False,
                                      max_length=255,
                                      widget=forms.TextInput())
            self.fields['addon'] = field

        if 'troubleshooting' in extra_fields:
            widget = forms.Textarea(attrs={'class': 'troubleshooting'})
            field = StrippedCharField(label=TROUBLESHOOTING_LABEL,
                                      help_text=TROUBLESHOOTING_HELP,
                                      required=False,
                                      max_length=30000,
                                      widget=widget)
            self.fields['troubleshooting'] = field

        if 'ff_version' in extra_fields:
            field = StrippedCharField(label=FF_VERSION_LABEL, required=False)
            self.fields['ff_version'] = field

        if 'os' in extra_fields:
            self.fields['os'] = StrippedCharField(label=OS_LABEL,
                                                  required=False)

        if 'plugins' in extra_fields:
            widget = forms.Textarea(attrs={'class': 'plugins'})
            self.fields['plugins'] = StrippedCharField(label=PLUGINS_LABEL,
                                                       required=False,
                                                       widget=widget)

    @property
    def metadata_field_keys(self):
        """Returns the keys of the metadata fields for the current
        form instance"""
        non_metadata_fields = ['title', 'content', 'email']
        metadata_filter = lambda x: x not in non_metadata_fields
        return filter(metadata_filter, self.fields.keys())

    @property
    def cleaned_metadata(self):
        """Returns a dict with cleaned metadata values.  Omits
        fields with empty string value."""
        clean = {}
        for key in self.metadata_field_keys:
            if key in self.data and self.data[key] != u'':
                clean[key] = self.cleaned_data[key]
        return clean


class NewQuestionForm(EditQuestionForm):
    """Form to start a new question"""

    def __init__(self, user=None, product=None, category=None, *args,
                 **kwargs):
        """Add fields particular to new questions."""
        super(NewQuestionForm, self).__init__(user, product, category, *args,
                                              **kwargs)

        # Collect user agent only when making a question for the first time.
        # Otherwise, we could grab moderators' user agents.
        self.fields['useragent'] = forms.CharField(widget=forms.HiddenInput(),
                                                   required=False)


class AnswerForm(forms.Form):
    """Form for replying to a question."""
    content = StrippedCharField(
                min_length=5,
                max_length=10000,
                widget=forms.Textarea(),
                error_messages={'required': MSG_CONTENT_REQUIRED,
                                'min_length': MSG_CONTENT_SHORT,
                                'max_length': MSG_CONTENT_LONG})

    class Meta:
        model = Answer
        fields = ('content',)


class WatchQuestionForm(forms.Form):
    """Form to subscribe to question updates."""
    EVENT_TYPE_CHOICES = (
        ('reply', 'when anybody replies.'),
        ('solution', 'when a solution is found.'),
    )

    email = forms.EmailField()
    event_type = forms.ChoiceField(choices=EVENT_TYPE_CHOICES,
                                   widget=forms.RadioSelect)

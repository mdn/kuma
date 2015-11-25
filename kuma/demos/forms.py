from django import forms
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect

from constance import config

from kuma.core.utils import parse_tags
from . import TAG_DESCRIPTIONS
from .models import Submission


SCREENSHOT_MAXW = getattr(settings, 'DEMO_SCREENSHOT_MAX_WIDTH', 480)
SCREENSHOT_MAXH = getattr(settings, 'DEMO_SCREENSHOT_MAX_HEIGHT', 360)


class MyModelForm(forms.ModelForm):
    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row=u'<li%(html_class_attr)s>%(label)s %(field)s%(help_text)s%(errors)s</li>',
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)


class MyForm(forms.Form):
    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row=u'<li%(html_class_attr)s>%(label)s %(field)s%(help_text)s%(errors)s</li>',
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)


class SubmissionEditForm(MyModelForm):
    """Form accepting demo submissions"""

    class Meta:
        model = Submission
        widgets = {
            'navbar_optout': forms.Select
        }
        fields = (
            'title', 'summary', 'description', 'hidden',
            'tech_tags', 'challenge_tags',
            'screenshot_1', 'screenshot_2', 'screenshot_3',
            'screenshot_4', 'screenshot_5',
            'video_url', 'navbar_optout',
            'demo_package', 'source_code_url', 'license_name',
        )

    # Assemble tech tag choices from TAG_DESCRIPTIONS
    tech_tags = forms.MultipleChoiceField(
        label="Tech tags",
        widget=CheckboxSelectMultiple,
        required=False,
        choices=(
            (x['tag_name'], x['title'])
            for x in TAG_DESCRIPTIONS.values()
            if x['tag_name'].startswith('tech:')
        )
    )

    challenge_tags = forms.ChoiceField(
        label="Dev Derby Challenge tag",
        widget=RadioSelect,
        required=False,
    )

    def __init__(self, *args, **kwargs):

        # Set the request user, for tag namespace permissions
        self.request_user = kwargs.pop('request_user', AnonymousUser)

        # Hit up the super class for init
        super(SubmissionEditForm, self).__init__(*args, **kwargs)

        self.fields['challenge_tags'].choices = (
            (TAG_DESCRIPTIONS[x]['tag_name'], TAG_DESCRIPTIONS[x]['title'])
            for x in parse_tags(
                'challenge:none %s' %
                config.DEMOS_DEVDERBY_CHALLENGE_CHOICE_TAGS,
                sorted=False)
            if x in TAG_DESCRIPTIONS
        )

        # If this is being used to edit a submission, we need to do
        # the following:
        #
        # 1. Populate the tech tags.
        #
        # 2. If the deadline has passed for the challenge this is
        #    entered in, remove the 'demo_package' field since they
        #    can't upload a new package past the deadline.
        #
        # 3. If the deadline has passed, remove the field for choosing
        #    which derby they're entered in. Otherwise, populate it so
        #    they can choose to change it.
        #
        # 4. Make sure we stash away the existing challenge tags, and
        #    ensure they're preserved across the edit.
        instance = kwargs.get('instance', None)
        if instance:
            if instance.is_derby_submission():
                if instance.challenge_closed():
                    for fieldname in ('demo_package', 'challenge_tags'):
                        del self.fields[fieldname]
                    self._old_challenge_tags = [unicode(tag) for tag in instance.taggit_tags.all_ns('challenge:')]
            for ns in ('tech', 'challenge'):
                if '%s_tags' % ns in self.fields:
                    self.initial['%s_tags' % ns] = [
                        t.name
                        for t in instance.taggit_tags.all_ns('%s:' % ns)]

    def clean(self):
        cleaned_data = super(SubmissionEditForm, self).clean()

        # If we have a demo_package, try validating it.
        if 'demo_package' in self.files:
            try:
                demo_package = self.files['demo_package']
                Submission.validate_demo_zipfile(demo_package)
            except ValidationError, e:
                self._errors['demo_package'] = self.error_class(e.messages)

        return cleaned_data

    def save(self, commit=True):
        rv = super(SubmissionEditForm, self).save(commit)

        # HACK: Since django.forms.models does this in a hack, we have to mimic
        # the hack to override it.
        super_save_m2m = hasattr(self, 'save_m2m') and self.save_m2m or None

        def save_m2m():
            if super_save_m2m:
                super_save_m2m()
            self.instance.taggit_tags.set_ns('tech:', *self.cleaned_data.get('tech_tags', []))
            # Look for a dev derby tag first in cleaned_data; if it
            # doesn't exist there, see if we stashed away the tags
            # from the instance; if not, fall back to empty list. This
            # is slightly verbose because we do have to handle the
            # legacy case of multiple challenge tags even though we
            # now only allow one per demo.
            if 'challenge_tags' in self.cleaned_data and self.cleaned_data['challenge_tags']:
                # We have to do the check like this because otherwise
                # we get false positive from challenge_tags being an
                # empty string.
                challenge_tags = [self.cleaned_data['challenge_tags']]
            else:
                challenge_tags = getattr(self, '_old_challenge_tags', [])
            if challenge_tags:
                self.instance.taggit_tags.set_ns('challenge:', *challenge_tags)

        if commit:
            save_m2m()
        else:
            self.save_m2m = save_m2m

        return rv


class SubmissionNewForm(SubmissionEditForm):

    class Meta(SubmissionEditForm.Meta):
        fields = SubmissionEditForm.Meta.fields + ('accept_terms', )

    accept_terms = forms.BooleanField(initial=False, required=True)

    def __init__(self, *args, **kwargs):
        super(SubmissionNewForm, self).__init__(*args, **kwargs)

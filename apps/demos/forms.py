from hashlib import md5

import zipfile
import tarfile

from django import forms

from django.utils.encoding import smart_unicode, smart_str

from django.conf import settings

from django.utils.translation import ugettext_lazy as _

from django.db import models

from django.contrib.auth.models import User, AnonymousUser

from django.core.exceptions import ObjectDoesNotExist
from django.core import validators
from django.core.exceptions import ValidationError
#from uni_form.helpers import FormHelper, Submit, Reset
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

from . import scale_image
from .models import Submission, TAG_DESCRIPTIONS, TAG_NAMESPACE_DEMO_CREATOR_WHITELIST

from captcha.fields import ReCaptchaField

import django.forms.fields
from django.forms.widgets import CheckboxSelectMultiple

import tagging.forms
from tagging.utils import parse_tag_input

from taggit.utils import parse_tags


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from PIL import Image
except ImportError:
    import Image


SCREENSHOT_MAXW  = getattr(settings, 'DEMO_SCREENSHOT_MAX_WIDTH', 480)
SCREENSHOT_MAXH = getattr(settings, 'DEMO_SCREENSHOT_MAX_HEIGHT', 360)


class MyModelForm(forms.ModelForm):
    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row = u'<li%(html_class_attr)s>%(label)s %(field)s%(help_text)s%(errors)s</li>',
            error_row = u'<li>%s</li>',
            row_ender = '</li>',
            help_text_html = u' <p class="help">%s</p>',
            errors_on_separate_row = False)


class MyForm(forms.Form):
    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row = u'<li%(html_class_attr)s>%(label)s %(field)s%(help_text)s%(errors)s</li>',
            error_row = u'<li>%s</li>',
            row_ender = '</li>',
            help_text_html = u' <p class="help">%s</p>',
            errors_on_separate_row = False)


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
        label = "Tech tags",
        widget = CheckboxSelectMultiple,
        required = False,
        choices = ( 
            (x['tag_name'], x['title']) 
            for x in TAG_DESCRIPTIONS.values() 
            if x['tag_name'].startswith('tech:')
        )
    )

    challenge_tags = forms.MultipleChoiceField(
        label = "Dev Derby Challenge tags",
        widget = CheckboxSelectMultiple,
        required = False,
        choices = (
            (x['tag_name'], x['title']) 
            for x in TAG_DESCRIPTIONS.values() 
            if x['tag_name'].startswith('challenge:')
        )
    )

    def __init__(self, *args, **kwargs):

        # Set the request user, for tag namespace permissions
        self.request_user = kwargs.get('request_user', AnonymousUser)
        del kwargs['request_user']

        # Hit up the super class for init
        super(SubmissionEditForm, self).__init__(*args, **kwargs)

        if 'instance' in kwargs and kwargs['instance']:
            # If we have an instance, try populating the user-accessible namespace
            # form fields with exiating tags.
            tags_incoming = ( 
                ( self.instance.pk is not None )
                and [ x.name for x in self.instance.taggit_tags.all() ]
                or [ ]
            )
        elif 'tags' in self.initial:
            # If we have tags in the initial data set, use those to populate
            # user-accessible namespaces.
            tags_incoming = parse_tags(self.initial['tags'])
        else:
            # No tags for pre-population
            tags_incoming = []

        # Use any incoming tags to prepopulate the form.
        if tags_incoming:
            for ns in TAG_NAMESPACE_DEMO_CREATOR_WHITELIST:
                self.initial['%s_tags' % ns[:-1]] = [
                    x for x in tags_incoming if x.startswith(ns)
                ]

    def clean(self):
        cleaned_data = super(SubmissionEditForm, self).clean()

        # Establish a set of tags, if none available
        if 'tags' not in cleaned_data:
            cleaned_data['tags'] = []

        # If there are *_tags fields, append them as tags.
        for k in cleaned_data:
            if k.endswith('_tags'):
                cleaned_data['tags'].extend(cleaned_data[k])

        # If we have an instance, apply the submitted tags as per the permissions.
        if self.instance:
            tags_orig = ( 
                ( self.instance.pk is not None )
                and [ x.name for x in self.instance.taggit_tags.all() ]
                or [ ]
            )
            cleaned_data['tags'] = self.instance.resolve_allowed_tags(
                tags_orig, cleaned_data['tags'], self.request_user 
            )

        # If we have a demo_package, try validating it.
        if 'demo_package' in self.files:
            try:
                demo_package = self.files['demo_package']
                Submission.validate_demo_zipfile(demo_package)
            except ValidationError, e:
                self._errors['demo_package'] = self.error_class(e.messages)

        return cleaned_data

    def save(self, commit=True):
        rv = super(SubmissionEditForm,self).save(commit)
        if commit:
            # Set the tags, if we have a go to commit.
            self.instance.taggit_tags.set(*self.cleaned_data['tags'])
        return rv


class SubmissionNewForm(SubmissionEditForm):

    class Meta(SubmissionEditForm.Meta):
        fields = SubmissionEditForm.Meta.fields + ( 'captcha', 'accept_terms', )

    captcha = ReCaptchaField(label=_("Show us you're human")) 
    accept_terms = forms.BooleanField(initial=False, required=True)


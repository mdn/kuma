from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from tower import ugettext_lazy as _
from taggit.utils import parse_tags

from devmo.models import UserProfile


class PrefixedURLField(forms.URLField):
    """URLField which also enforces a base URL prefix"""

    def __init__(self, *args, **kwargs):
        self.prefix = kwargs['prefix']
        del kwargs['prefix']
        return super(PrefixedURLField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value == self.prefix:
            return ''
        return super(PrefixedURLField, self).to_python(value)

    def validate(self, value):
        """Ensure the URL value starts with the given prefix"""
        super(PrefixedURLField, self).validate(value)
        if (self.required or value) and not value.startswith(self.prefix):
            raise ValidationError(_("URL should begin with %s") %
                                    self.prefix)


class UserProfileEditForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('fullname', 'title', 'organization', 'location',
                  'locale', 'timezone', 'bio', 'irc_nickname', 'interests')

    # Email is on the form, but is handled in the view separately
    email = forms.EmailField(label=_('Email'), required=True)

    interests = forms.CharField(label=_('Interests'),
                                max_length=255, required=False)
    expertise = forms.CharField(label=_('Expertise'),
                                max_length=255, required=False)
    locale = forms.ChoiceField(required=False,
                             choices=settings.LANGUAGE_CHOICES)

    def __init__(self, *args, **kwargs):
        super(UserProfileEditForm, self).__init__(*args, **kwargs)

        # Dynamically add URLFields for all sites defined in the model.
        sites = kwargs.get('sites', UserProfile.website_choices)
        for name, meta in sites:
            self.fields['websites_%s' % name] = PrefixedURLField(
                    prefix=meta['prefix'], required=False)

    def clean_expertise(self):
        """Enforce expertise as a subset of interests"""
        cleaned_data = self.cleaned_data

        # bug 709938 - don't assume interests passed validation
        interests = set(parse_tags(cleaned_data.get('interests','')))
        expertise = set(parse_tags(cleaned_data['expertise']))

        if len(expertise) > 0 and not expertise.issubset(interests):
            raise forms.ValidationError(_("Areas of expertise must be a "
                "subset of interests"))

        return cleaned_data['expertise']

    def clean_timezone(self):
        pass

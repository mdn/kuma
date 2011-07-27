import logging

from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import authenticate, forms as auth_forms
from django.contrib.auth.models import User

from tower import ugettext_lazy as _

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
        fields = ('fullname', 'title', 'organization', 'location', 'bio',
                  'interests')

    # Email is on the form, but is handled in the view separately
    email = forms.EmailField(label=_('Email'), required=True)

    def __init__(self, *args, **kwargs):
        super(UserProfileEditForm, self).__init__(*args, **kwargs)

        # Dynamically add URLFields for all sites defined in the model.
        sites = kwargs.get('sites', UserProfile.website_choices)
        for name, meta in sites:
            self.fields['websites_%s' % name] = PrefixedURLField(
                    prefix=meta['prefix'], required=False)

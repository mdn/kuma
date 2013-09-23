from django import forms
from django.contrib.auth.models import User, Group

import constance.config
from tower import ugettext_lazy as _
from taggit.utils import parse_tags

from devmo.models import UserProfile


class UserProfileEditForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('fullname', 'title', 'organization', 'location',
                  'locale', 'timezone', 'bio', 'irc_nickname', 'interests')

    beta = forms.BooleanField(label=_('Beta User'), required=False)

    # Email is on the form, but is handled in the view separately
    email = forms.EmailField(label=_('Email'), required=True)

    interests = forms.CharField(label=_('Interests'),
                                max_length=255, required=False)
    expertise = forms.CharField(label=_('Expertise'),
                                max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        super(UserProfileEditForm, self).__init__(*args, **kwargs)

        # Dynamically add URLFields for all sites defined in the model.
        sites = kwargs.get('sites', UserProfile.website_choices)
        for name, meta in sites:
            self.fields['websites_%s' % name] = forms.RegexField(
                    regex=meta['regex'], required=False)
            self.fields['websites_%s' % name].widget.attrs['placeholder'] = meta['prefix']

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

    def save(self, commit=True):
        try:
            user = User.objects.get(email=self.cleaned_data.get('email'))
            beta_group = Group.objects.get(
                name=constance.config.BETA_GROUP_NAME)
            if self.cleaned_data['beta']:
                beta_group.user_set.add(user)
            else:
                beta_group.user_set.remove(user)
        except Group.DoesNotExist:
            # If there's no Beta Testers group, ignore that logic
            pass
        return super(UserProfileEditForm, self).save(commit=True)

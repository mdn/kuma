from django import forms
from django.contrib.auth.models import User, Group

import constance.config
from tower import ugettext_lazy as _
from taggit.utils import parse_tags

from devmo.models import UserProfile
from product_details import product_details


EMAIL_REQUIRED = _(u'Email address is required.')
EMAIL_SHORT = _(u'Email address is too short (%(show_value)s characters). '
                    'It must be at least %(limit_value)s characters.')
EMAIL_LONG = _(u'Email address is too long (%(show_value)s characters). '
                   'It must be %(limit_value)s characters or less.')
PRIVACY_REQUIRED = _(u'You must agree to the privacy policy.')


class SubscriptionForm(forms.Form):
    """
    Form to capture and validate email subscriptions
    """
    email = forms.EmailField(label=_(u'E-mail address'),
                             error_messages={'required': EMAIL_REQUIRED,
                                             'min_length': EMAIL_SHORT,
                                             'max_length': EMAIL_LONG})

    formatChoices = [('html', 'HTML'), ('text', 'Plain text')]
    format = forms.ChoiceField(
        label=_(u'Preferred format'),
        choices=formatChoices,
        initial=formatChoices[0],
        widget=forms.RadioSelect()
    )
    agree = forms.BooleanField(
        label=_(u'I agree'),
        error_messages={'required': PRIVACY_REQUIRED}
    )

    def __init__(self, locale, *args, **kwargs):
        regions = product_details.get_regions(locale)
        regions = sorted(regions.iteritems(), key=lambda x: x[1])

        lang = country = locale.lower()
        if '-' in lang:
            lang, country = lang.split('-', 1)

        super(SubscriptionForm, self).__init__(*args, **kwargs)

        self.fields['country'] = forms.ChoiceField(
            label=_(u'Your country'),
            choices=regions,
            initial=country,
            required=False
        )


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

import operator
import time

from django import forms
from django.conf import settings
from django.http import HttpResponseServerError
from django.contrib.auth import get_user_model

import basket
from basket.base import BasketException
from basket.errors import BASKET_UNKNOWN_EMAIL
from constance import config
from product_details import product_details
from taggit.utils import parse_tags
from tower import ugettext_lazy as _

from .constants import USERNAME_CHARACTERS, USERNAME_REGEX
from .models import UserProfile

PRIVACY_REQUIRED = _(u'You must agree to the privacy policy.')


class NewsletterForm(forms.Form):
    """
    The base form class to be used for the signup form below as well as
    in standalone mode on the user profile editing page.

    It populates the country choices with the product_details database
    depending on the current request's locale.
    """
    FORMAT_HTML = 'html'
    FORMAT_TEXT = 'text'
    FORMAT_CHOICES = [
        (FORMAT_HTML, _(u'HTML')),
        (FORMAT_TEXT, _(u'Plain text')),
    ]
    newsletter = forms.BooleanField(label=_(u'Send me the newsletter'),
                                    required=False)
    format = forms.ChoiceField(label=_(u'Preferred format'),
                               choices=FORMAT_CHOICES,
                               initial=FORMAT_HTML,
                               widget=forms.RadioSelect(attrs={'id': 'format'}),
                               required=False)
    agree = forms.BooleanField(label=_(u'I agree'),
                               required=False,
                               error_messages={'required': PRIVACY_REQUIRED})
    country = forms.ChoiceField(label=_(u'Your country'),
                                choices=[],
                                required=False)

    def __init__(self, locale, already_subscribed, *args, **kwargs):
        super(NewsletterForm, self).__init__(*args, **kwargs)
        self.already_subscribed = already_subscribed

        regions = product_details.get_regions(locale)
        regions = sorted(regions.iteritems(), key=operator.itemgetter(1))

        lang = country = locale.lower()
        if '-' in lang:
            lang, country = lang.split('-', 1)

        self.fields['country'].choices = regions
        self.fields['country'].initial = country

    def clean(self):
        cleaned_data = super(NewsletterForm, self).clean()
        if cleaned_data['newsletter'] and not self.already_subscribed:
            if cleaned_data['agree']:
                cleaned_data['subscribe_needed'] = True
            else:
                raise forms.ValidationError(PRIVACY_REQUIRED)
        return cleaned_data

    def signup(self, request, user):
        """
        Used by allauth when successfully signing up a user. This will
        be ignored if this form is used standalone.
        """
        self.subscribe(request, user.email)

    @classmethod
    def is_subscribed(cls, email):
        subscription_details = cls.get_subscription_details(email)
        return (settings.BASKET_APPS_NEWSLETTER in
                subscription_details['newsletters']
                if subscription_details
                else False)

    @classmethod
    def get_subscription_details(cls, email):
        subscription_details = None
        try:
            api_key = config.BASKET_API_KEY
            subscription_details = basket.lookup_user(email=email,
                                                      api_key=api_key)
        except BasketException, e:
            if e.code == BASKET_UNKNOWN_EMAIL:
                # pass - unknown email is just a new subscriber
                pass
        return subscription_details

    def subscribe(self, request, email):
        subscription_details = self.get_subscription_details(email)
        if 'subscribe_needed' in self.cleaned_data:
            optin = 'N'
            if request.locale == 'en-US':
                optin = 'Y'
            basket_data = {
                'email': email,
                'newsletters': settings.BASKET_APPS_NEWSLETTER,
                'country': self.cleaned_data['country'],
                'format': self.cleaned_data['format'],
                'lang': request.locale,
                'optin': optin,
                'source_url': request.build_absolute_uri()
            }
            for retry in range(config.BASKET_RETRIES):
                try:
                    result = basket.subscribe(**basket_data)
                    if result.get('status') != 'error':
                        break
                except BasketException:
                    if retry == config.BASKET_RETRIES:
                        return HttpResponseServerError()
                    else:
                        time.sleep(config.BASKET_RETRY_WAIT * retry)
        elif subscription_details:
            basket.unsubscribe(subscription_details['token'], email,
                               newsletters=settings.BASKET_APPS_NEWSLETTER)


class UserBanForm(forms.Form):
    """
    The form used in the view that enables admins to ban users.
    """
    reason = forms.CharField(widget=forms.Textarea)


class UserProfileEditForm(forms.ModelForm):
    """
    The main form to edit user profile data.

    It dynamically adds a bunch of fields for maintaining information
    about a user's websites and handles expertise and interests fields
    specially.
    """
    beta = forms.BooleanField(label=_(u'Beta tester'), required=False)
    interests = forms.CharField(label=_(u'Interests'),
                                max_length=255, required=False,
                                widget=forms.TextInput(attrs={'class': 'tags'}))
    expertise = forms.CharField(label=_(u'Expertise'),
                                max_length=255, required=False,
                                widget=forms.TextInput(attrs={'class': 'tags'}))
    username = forms.RegexField(label=_(u'Username'), regex=USERNAME_REGEX,
                                max_length=30, required=False,
                                error_message=USERNAME_CHARACTERS)

    class Meta:
        model = UserProfile
        fields = ('fullname', 'title', 'organization', 'location',
                  'locale', 'timezone', 'bio', 'irc_nickname', 'interests')

    def __init__(self, *args, **kwargs):
        super(UserProfileEditForm, self).__init__(*args, **kwargs)
        # Dynamically add URLFields for all sites defined in the model.
        sites = kwargs.get('sites', UserProfile.website_choices)
        for name, meta in sites:
            self.fields['websites_%s' % name] = forms.RegexField(regex=meta['regex'], required=False)
            self.fields['websites_%s' % name].widget.attrs['placeholder'] = meta['prefix']

    def clean_expertise(self):
        """Enforce expertise as a subset of interests"""
        # bug 709938 - don't assume interests passed validation
        interests = set(parse_tags(self.cleaned_data.get('interests', '')))
        expertise = set(parse_tags(self.cleaned_data['expertise']))

        if len(expertise) > 0 and not expertise.issubset(interests):
            raise forms.ValidationError(_("Areas of expertise must be a "
                                          "subset of interests"))

        return self.cleaned_data['expertise']

    def clean_username(self):
        new_username = self.cleaned_data['username']

        if (self.instance is not None and
                get_user_model().objects
                                .exclude(pk=self.instance.user.pk)
                                .filter(username=new_username)
                                .exists()):
            raise forms.ValidationError(_('Username already in use.'))
        return new_username

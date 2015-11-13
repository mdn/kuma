import operator
import time

import basket
from basket.base import BasketException
from basket.errors import BASKET_UNKNOWN_EMAIL
from constance import config
from django import forms
from django.conf import settings
from django.http import HttpResponseServerError
from django.utils.translation import ugettext_lazy as _
from product_details import product_details
from sundial.forms import TimezoneChoiceField
from sundial.zones import COMMON_GROUPED_CHOICES
from taggit.utils import parse_tags

from .constants import (USERNAME_CHARACTERS,
                        USERNAME_LEGACY_REGEX, USERNAME_REGEX)
from .models import User

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
        except BasketException as e:
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


class UserEditForm(forms.ModelForm):
    """
    The main form to edit user profile data.

    It dynamically adds a bunch of fields for maintaining information
    about a user's websites and handles expertise and interests fields
    specially.
    """
    timezone = TimezoneChoiceField(
        label=_(u'Timezone'),
        initial=settings.TIME_ZONE,
        choices=COMMON_GROUPED_CHOICES,
        required=False,
    )
    beta = forms.BooleanField(
        label=_(u'Beta tester'),
        required=False,
    )
    interests = forms.CharField(
        label=_(u'Interests'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'tags'}),
    )
    expertise = forms.CharField(
        label=_(u'Expertise'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'tags'}),
    )
    username = forms.RegexField(
        label=_(u'Username'),
        regex=USERNAME_REGEX,
        max_length=30,
        required=False,
        error_message=USERNAME_CHARACTERS,
    )
    website_url = forms.CharField(
        label=_('Website'),
        required=False,
        validators=[User.WEBSITE_VALIDATORS['website']],
        widget=forms.TextInput(attrs={
            'placeholder': 'http://',
            'data-fa-icon': 'icon-link',
        }),
    )
    twitter_url = forms.CharField(
        label=_('Twitter'),
        required=False,
        validators=[User.WEBSITE_VALIDATORS['twitter']],
        widget=forms.TextInput(attrs={
            'placeholder': 'https://twitter.com/',
            'data-fa-icon': 'icon-twitter',
        }),
    )
    github_url = forms.CharField(
        label=_('GitHub'),
        required=False,
        validators=[User.WEBSITE_VALIDATORS['github']],
        widget=forms.TextInput(attrs={
            'placeholder': 'https://github.com/',
            'data-fa-icon': 'icon-github',
        }),
    )
    stackoverflow_url = forms.CharField(
        label=_('Stack Overflow'),
        required=False,
        validators=[User.WEBSITE_VALIDATORS['stackoverflow']],
        widget=forms.TextInput(attrs={
            'placeholder': 'https://stackoverflow.com/users/',
            'data-fa-icon': 'icon-stackexchange',
        }),
    )
    linkedin_url = forms.CharField(
        label=_('LinkedIn'),
        required=False,
        validators=[User.WEBSITE_VALIDATORS['linkedin']],
        widget=forms.TextInput(attrs={
            'placeholder': 'https://www.linkedin.com/',
            'data-fa-icon': 'icon-linkedin',
        }),
    )
    mozillians_url = forms.CharField(
        label=_('Mozillians'),
        required=False,
        validators=[User.WEBSITE_VALIDATORS['mozillians']],
        widget=forms.TextInput(attrs={
            'placeholder': 'https://mozillians.org/u/',
            'data-fa-icon': 'icon-group',
        }),
    )
    facebook_url = forms.CharField(
        label=_('Facebook'),
        required=False,
        validators=[User.WEBSITE_VALIDATORS['facebook']],
        widget=forms.TextInput(attrs={
            'placeholder': 'https://www.facebook.com/',
            'data-fa-icon': 'icon-facebook',
        }),
    )

    class Meta:
        model = User
        fields = ('fullname', 'title', 'organization', 'location',
                  'locale', 'timezone', 'bio', 'irc_nickname', 'interests',
                  'website_url', 'twitter_url', 'github_url',
                  'stackoverflow_url', 'linkedin_url', 'mozillians_url',
                  'facebook_url', 'username')

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        # in case the username is not changed and the user has a legacy
        # username we want to disarm the username regex
        if ('username' not in self.changed_data and
                self.instance and self.instance.has_legacy_username):
            self.fields['username'].regex = USERNAME_LEGACY_REGEX

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

        if not new_username:
            raise forms.ValidationError(_('This field cannot be blank.'))

        if (self.instance is not None and
                User.objects.exclude(pk=self.instance.pk)
                            .filter(username=new_username)
                            .exists()):
            raise forms.ValidationError(_('Username already in use.'))
        return new_username

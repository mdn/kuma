import time

from django import forms
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponseServerError

import basket
from basket.base import BasketException
from basket.errors import BASKET_UNKNOWN_EMAIL
import constance.config
from tower import ugettext_lazy as _
from product_details import product_details
from taggit.utils import parse_tags

from landing.forms import PRIVACY_REQUIRED

from .models import UserProfile


USERNAME_INVALID = _(u'User name may contain only letters, '
                     u'numbers, and these characters: . - _')
USERNAME_REQUIRED = _(u'Username is required.')
USERNAME_SHORT = _(u'Username is too short (%(show_value)s characters). '
                   u'It must be at least %(limit_value)s characters.')
USERNAME_LONG = _(u'Username is too long (%(show_value)s characters). '
                  u'It must be %(limit_value)s characters or less.')
EMAIL_REQUIRED = _(u'Email address is required.')
EMAIL_SHORT = _(u'Email address is too short (%(show_value)s characters). '
                u'It must be at least %(limit_value)s characters.')
EMAIL_LONG = _(u'Email address is too long (%(show_value)s characters). '
               u'It must be %(limit_value)s characters or less.')
PASSWD_REQUIRED = _(u'Password is required.')
PASSWD2_REQUIRED = _(u'Please enter your password twice.')
PASSWD_UTF8 = _(u'To use this password, you need to initiate a password '
                u'reset. Please use the "forgot my password" link below.')


class UsernameField(forms.RegexField):
    def __init__(self, *args, **kwargs):
        super(UsernameField, self).__init__(
            label=_(u'Username'), max_length=30, min_length=3,
            regex=r'^[\w.-]+$',
            help_text=_(u'Required. 30 characters or fewer. '
                        u'Letters, digits and ./-/_ only.'),
            widget=forms.TextInput(),
            error_messages={'invalid': USERNAME_INVALID,
                            'required': USERNAME_REQUIRED,
                            'min_length': USERNAME_SHORT,
                            'max_length': USERNAME_LONG},
            *args, **kwargs)


class BrowserIDRegisterForm(forms.ModelForm):
    """A user registration form that only requires a username, since BrowserID
    supplies the email address and no password is necessary."""

    username = UsernameField()

    newsletter = forms.BooleanField(label=_(u'Send me the newsletter'),
                                    required=False)

    # Newsletter fields copied from SubscriptionForm
    formatChoices = [('html', 'HTML'), ('text', 'Plain text')]
    format = forms.ChoiceField(
        label=_(u'Preferred format'),
        choices=formatChoices,
        initial=formatChoices[0],
        widget=forms.RadioSelect()
    )
    agree = forms.BooleanField(
        label=_(u'I agree'),
        error_messages={'required': PRIVACY_REQUIRED},
        required=False
    )

    class Meta(object):
        model = User
        fields = ('username',)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_(u'The username you entered '
                                          u'already exists.'))
        return username

    def __init__(self, locale, request=None, *args, **kwargs):
        regions = product_details.get_regions(locale)
        regions = sorted(regions.iteritems(), key=lambda x: x[1])
        self.locale = locale

        lang = country = locale.lower()
        if '-' in lang:
            lang, country = lang.split('-', 1)
        super(BrowserIDRegisterForm, self).__init__(request, *args, **kwargs)

        # Newsletter field copied from SubscriptionForm
        self.fields['country'] = forms.ChoiceField(
            label=_(u'Your country'),
            choices=regions,
            initial=country,
            required=False
        )


class UserBanForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea)


class UserProfileEditForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('fullname', 'title', 'organization', 'location',
                  'locale', 'timezone', 'bio', 'irc_nickname', 'interests')

    beta = forms.BooleanField(label=_(u'Beta tester'), required=False)

    # Email is on the form, but is handled in the view separately
    email = forms.EmailField(label=_(u'Email'), required=True)

    interests = forms.CharField(label=_(u'Interests'),
                                max_length=255, required=False)
    expertise = forms.CharField(label=_(u'Expertise'),
                                max_length=255, required=False)

    newsletter = forms.BooleanField(label=_(u'Send me the newsletter'),
                                    required=False)

    # Newsletter fields copied from SubscriptionForm
    formatChoices = [('html', 'HTML'), ('text', 'Plain text')]
    format = forms.ChoiceField(
        label=_(u'Preferred format'),
        choices=formatChoices,
        initial=formatChoices[0],
        widget=forms.RadioSelect()
    )
    agree = forms.BooleanField(
        label=_(u'I agree'),
        error_messages={'required': PRIVACY_REQUIRED},
        required=False
    )

    def __init__(self, locale, *args, **kwargs):
        regions = product_details.get_regions(locale)
        regions = sorted(regions.iteritems(), key=lambda x: x[1])
        self.locale = locale

        lang = country = locale.lower()
        if '-' in lang:
            lang, country = lang.split('-', 1)

        super(UserProfileEditForm, self).__init__(*args, **kwargs)

        # Dynamically add URLFields for all sites defined in the model.
        sites = kwargs.get('sites', UserProfile.website_choices)
        for name, meta in sites:
            self.fields['websites_%s' % name] = forms.RegexField(
                    regex=meta['regex'], required=False)
            self.fields['websites_%s' % name].widget.attrs['placeholder'] = meta['prefix']

        # Newsletter field copied from SubscriptionForm
        # FIXME: this is extra dupe nasty here because we already have a locale
        # field on the profile
        self.fields['country'] = forms.ChoiceField(
            label=_(u'Your country'),
            choices=regions,
            initial=country,
            required=False
        )

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
        email = self.cleaned_data.get('email')
        try:
            # Beta
            user = User.objects.get(email=email)
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


def newsletter_subscribe(request, email, cleaned_data):
    subscription_details = get_subscription_details(email)
    subscribed = subscribed_to_newsletter(subscription_details)

    if cleaned_data['newsletter'] and not subscribed:
        if not cleaned_data['agree']:
            raise forms.ValidationError(PRIVACY_REQUIRED)
        optin = 'N'
        if request.locale == 'en-US':
            optin = 'Y'
        for i in range(constance.config.BASKET_RETRIES):
            try:
                result = basket.subscribe(
                        email=email,
                        newsletters=settings.BASKET_APPS_NEWSLETTER,
                        country=cleaned_data['country'],
                        format=cleaned_data['format'],
                        lang=request.locale,
                        optin=optin,
                        source_url=request.build_absolute_uri())
                if result.get('status') != 'error':
                    break
            except BasketException:
                if i == constance.config.BASKET_RETRIES:
                    return HttpResponseServerError()
                else:
                    time.sleep(constance.config.BASKET_RETRY_WAIT * i)
    elif subscription_details:
        basket.unsubscribe(subscription_details['token'], email,
                           newsletters=settings.BASKET_APPS_NEWSLETTER)


def get_subscription_details(email):
    subscription_details = None
    try:
        subscription_details = basket.lookup_user(email=email,
                                        api_key=constance.config.BASKET_API_KEY)
    except BasketException, e:
        if e.code == BASKET_UNKNOWN_EMAIL:
            # pass - unknown email is just a new subscriber
            pass
    return subscription_details


def subscribed_to_newsletter(subscription_details):
    subscribed = (settings.BASKET_APPS_NEWSLETTER in
                  subscription_details['newsletters'] if
                  subscription_details else False)
    return subscribed

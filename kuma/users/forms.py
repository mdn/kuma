import operator
import time

from django import forms
from django.conf import settings
from django.http import HttpResponseServerError

import basket
from basket.base import BasketException
from basket.errors import BASKET_UNKNOWN_EMAIL
import constance.config
from product_details import product_details
from taggit.utils import parse_tags
from tower import ugettext_lazy as _


from .models import UserProfile


EMAIL_REQUIRED = _(u'Email address is required.')
EMAIL_SHORT = _(u'Email address is too short (%(show_value)s characters). '
                u'It must be at least %(limit_value)s characters.')
EMAIL_LONG = _(u'Email address is too long (%(show_value)s characters). '
               u'It must be %(limit_value)s characters or less.')
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

    def __init__(self, locale, *args, **kwargs):
        super(NewsletterForm, self).__init__(*args, **kwargs)

        regions = product_details.get_regions(locale)
        regions = sorted(regions.iteritems(), key=operator.itemgetter(1))

        lang = country = locale.lower()
        if '-' in lang:
            lang, country = lang.split('-', 1)

        self.fields['country'].choices = regions
        self.fields['country'].initial = country

    def signup(self, request, user):
        """
        Used by allauth when successfully signing up a user. This will
        be ignored if this form is used standalone.
        """
        newsletter_subscribe(request, user.email, self.cleaned_data)


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
                                max_length=255, required=False)
    expertise = forms.CharField(label=_(u'Expertise'),
                                max_length=255, required=False)

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

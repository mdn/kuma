import re

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, forms as auth_forms
from django.contrib.auth.models import User

from tower import ugettext as _, ugettext_lazy as _lazy

from dekicompat.backends import DekiUserBackend
from sumo.widgets import ImageWidget
from upload.forms import clean_image_extension
from upload.utils import check_file_size, FileTooLargeError
from users.models import Profile
from users.widgets import FacebookURLWidget, TwitterURLWidget


USERNAME_INVALID = _lazy(u'Username may contain only letters, '
                         'numbers and @/./+/-/_ characters.')
USERNAME_REQUIRED = _lazy(u'Username is required.')
USERNAME_SHORT = _lazy(u'Username is too short (%(show_value)s characters). '
                       'It must be at least %(limit_value)s characters.')
USERNAME_LONG = _lazy(u'Username is too long (%(show_value)s characters). '
                      'It must be %(limit_value)s characters or less.')
EMAIL_REQUIRED = _lazy(u'Email address is required.')
EMAIL_SHORT = _lazy(u'Email address is too short (%(show_value)s characters). '
                    'It must be at least %(limit_value)s characters.')
EMAIL_LONG = _lazy(u'Email address is too long (%(show_value)s characters). '
                   'It must be %(limit_value)s characters or less.')
PASSWD_REQUIRED = _lazy(u'Password is required.')
PASSWD2_REQUIRED = _lazy(u'Please enter your password twice.')
PASSWD_UTF8 = _lazy(u'To use this password, you need to initiate a password '
                    u'reset. Please use the "forgot my password" link below.')


class UsernameField(forms.RegexField):
    def __init__(self, *args, **kwargs):
        super(UsernameField, self).__init__(
            label=_lazy(u'Username'), max_length=30, min_length=4,
            regex=r'^[\w.@+-]+$',
            help_text=_lazy(u'Required. 30 characters or fewer. '
                            'Letters, digits and @/./+/-/_ only.'),
            error_messages={'invalid': USERNAME_INVALID,
                            'required': USERNAME_REQUIRED,
                            'min_length': USERNAME_SHORT,
                            'max_length': USERNAME_LONG},
            *args, **kwargs)


class RegisterForm(forms.ModelForm):
    """A user registration form that requires unique email addresses.

    The default Django user creation form does not require an email address,
    let alone that it be unique. This form does, and sets a minimum length
    for usernames.

    """
    username = UsernameField()
    email = forms.EmailField(label=_lazy(u'Email address'),
                             error_messages={'required': EMAIL_REQUIRED,
                                             'min_length': EMAIL_SHORT,
                                             'max_length': EMAIL_LONG})
    password = forms.CharField(label=_lazy(u'Password'),
                               widget=forms.PasswordInput(
                                   render_value=False),
                               error_messages={'required': PASSWD_REQUIRED})
    password2 = forms.CharField(label=_lazy(u'Repeat password'),
                                widget=forms.PasswordInput(
                                    render_value=False),
                                error_messages={'required': PASSWD2_REQUIRED},
                                help_text=_lazy(u'Enter the same password as '
                                                 'above, for verification.'))

    class Meta(object):
        model = User
        fields = ('username', 'password', 'password2', 'email')

    def clean(self):
        super(RegisterForm, self).clean()
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if not password == password2:
            raise forms.ValidationError(_('Passwords must match.'))

        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email address '
                                          'already exists.'))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # check deki for existing user (it needs = in front of name)
        deki_user = DekiUserBackend.get_deki_user('=' + username)
        if deki_user is not None:
            raise forms.ValidationError(
                _('The username you entered already exists.'))
        return username

    def __init__(self,  request=None, *args, **kwargs):
        super(RegisterForm, self).__init__(request, auto_id='id_for_%s',
                                           *args, **kwargs)


class BrowserIDRegisterForm(forms.ModelForm):
    """A user registration form that only requires a username, since BrowserID
    supplies the email address and no password is necessary."""

    username = UsernameField()

    class Meta(object):
        model = User
        fields = ('username',)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # check deki for existing user (it needs = in front of name)
        deki_user = DekiUserBackend.get_deki_user('=' + username)
        if deki_user is not None:
            raise forms.ValidationError(_('The username you entered'
                                          ' already exists.'))
        return username

    def __init__(self,  request=None, *args, **kwargs):
        super(BrowserIDRegisterForm, self).__init__(request,
                                                    auto_id='id_for_%s',
                                                    *args, **kwargs)


class AuthenticationForm(auth_forms.AuthenticationForm):
    """Overrides the default django form.

    * Doesn't prefill password on validation error.
    * Allows logging in inactive users (initialize with `only_active=False`).
    """
    password = forms.CharField(label=_lazy(u"Password"),
                               widget=forms.PasswordInput(render_value=False))

    def __init__(self, request=None, only_active=True, *args, **kwargs):
        self.only_active = only_active
        super(AuthenticationForm, self).__init__(request, *args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                self.user_cache = authenticate(username=username,
                                               password=password)
            except UnicodeEncodeError:
                raise forms.ValidationError(PASSWD_UTF8)

            if self.user_cache is None:
                raise forms.ValidationError(
                    _('Please enter a correct username and password. Note '
                      'that both fields are case-sensitive.'))
            elif self.only_active and not self.user_cache.is_active:
                raise forms.ValidationError(_('This account is inactive.'))

        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(
                    _("Your Web browser doesn't appear to have cookies "
                      "enabled. Cookies are required for logging in."))

        return self.cleaned_data


class PasswordResetForm(auth_forms.PasswordResetForm):
    """Overrides the default django form.
    * Checks mindtouch for an email address
    * Creates django user & profile if needed
    """
    def clean_email(self):
        try:
            return super(PasswordResetForm, self).clean_email()
        except forms.ValidationError as e:
            email = self.cleaned_data["email"]
            deki_user = DekiUserBackend.get_deki_user_by_email(email)
            if deki_user is None:
                raise e
            else:
                user = DekiUserBackend.get_or_create_user(deki_user)
                self.users_cache = User.objects.filter(email__iexact=email)
                return user.email
            raise e


class ProfileForm(forms.ModelForm):
    """The form for editing the user's profile."""

    class Meta(object):
        model = Profile
        exclude = ('user', 'livechat_id', 'avatar')
        widgets = {
            'twitter': TwitterURLWidget,
            'facebook': FacebookURLWidget,
        }

    def clean_twitter(self):
        twitter = self.cleaned_data['twitter']
        if twitter and not re.match(TwitterURLWidget.pattern, twitter):
            raise forms.ValidationError(_(u'Please enter a twitter.com URL.'))
        return twitter

    def clean_facebook(self):
        facebook = self.cleaned_data['facebook']
        if facebook and not re.match(FacebookURLWidget.pattern, facebook):
            raise forms.ValidationError(_(u'Please enter a facebook.com URL.'))
        return facebook


class AvatarForm(forms.ModelForm):
    """The form for editing the user's avatar."""
    avatar = forms.ImageField(required=True, widget=ImageWidget)

    def __init__(self, *args, **kwargs):
        super(AvatarForm, self).__init__(*args, **kwargs)
        self.fields['avatar'].help_text = (
            u'Your avatar will be resized to {size}x{size}'.format(
                size=settings.AVATAR_SIZE))

    class Meta(object):
        model = Profile
        fields = ('avatar',)

    def clean_avatar(self):
        if not ('avatar' in self.cleaned_data and self.cleaned_data['avatar']):
            return self.cleaned_data['avatar']
        try:
            check_file_size(self.cleaned_data['avatar'],
                            settings.MAX_AVATAR_FILE_SIZE)
        except FileTooLargeError as e:
            raise forms.ValidationError(e.args[0])
        clean_image_extension(self.cleaned_data.get('avatar'))
        return self.cleaned_data['avatar']


class EmailConfirmationForm(forms.Form):
    """A simple form that requires an email address."""
    email = forms.EmailField(label=_lazy(u'Email address'))


class EmailReminderForm(forms.Form):
    """A simple form that requires a username."""
    username = UsernameField()


class EmailChangeForm(forms.Form):
    """A simple form that requires an email address and validates that it is
    not the current user's email."""
    email = forms.EmailField(label=_lazy(u'Email address'))

    def __init__(self, user, *args, **kwargs):
        super(EmailChangeForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.user.email == email:
            raise forms.ValidationError(_('This is your current email.'))
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email address '
                                          'already exists.'))
        return self.cleaned_data['email']

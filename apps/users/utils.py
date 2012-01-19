from django.conf import settings
from django.contrib import auth
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string

from tower import ugettext as _

from users.forms import RegisterForm, AuthenticationForm
from users.models import RegistrationProfile


def handle_login(request, only_active=True):
    auth.logout(request)

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST, only_active=only_active)
        if form.is_valid():
            auth.login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

        return form

    request.session.set_test_cookie()
    return AuthenticationForm()


def handle_register(request):
    """Handle to help registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            RegistrationProfile.objects.create_inactive_user(
                form.cleaned_data['username'], form.cleaned_data['password'],
                form.cleaned_data['email'])
        return form
    return RegisterForm()


def send_reminder_email(user):
    """Send a reminder email to the user."""
    subject = _('Email Address Reminder')
    email_template = 'users/email/reminder.ltxt'
    current_site = Site.objects.get_current()
    email_kwargs = {'username': user.username,
                    'domain': current_site.domain}
    message = render_to_string(email_template, email_kwargs)
    send_to = user.email
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [send_to])

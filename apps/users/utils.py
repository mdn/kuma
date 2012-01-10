from django.contrib import auth

import jingo

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
            try:
                RegistrationProfile.objects.create_inactive_user(
                    form.cleaned_data['username'], form.cleaned_data['password'],
                    form.cleaned_data['email'])
            except Exception:
                return jingo.render(request, '500.html',
                                    {'error_message': "We couldn't "
                                    "register a new account at this time. "
                                    "Please try again later."})
        return form
    return RegisterForm()

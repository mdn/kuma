from django.contrib import auth

from dekicompat.backends import DekiUserBackend
from users.forms import RegisterForm, AuthenticationForm
from users.models import RegistrationProfile


def handle_login(request, only_active=True):
    auth.logout(request)

    if request.method == 'POST':
        authtoken = DekiUserBackend.mindtouch_login(request)
        form = AuthenticationForm(data=request.POST, only_active=only_active, authtoken=authtoken)
        if form.is_valid():
            auth.login(request, form.get_user())
            request.session['mindtouch_authtoken'] = authtoken

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
        """
        elif authtoken:
            dub = DekiUserBackend()
            u = dub.authenticate(authtoken)
            auth.login(request, u)
            pass
        """

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

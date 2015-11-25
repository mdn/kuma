from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from allauth.account.models import EmailAddress

from kuma.core.tests import KumaTestCase, KumaTransactionTestCase


class UserTestMixin(object):
    """Base TestCase for the users app test cases."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(UserTestMixin, self).setUp()
        self.user_model = get_user_model()


class UserTestCase(UserTestMixin, KumaTestCase):
    pass


class UserTransactionTestCase(UserTestMixin, KumaTransactionTestCase):
    pass


def user(save=False, **kwargs):
    if 'username' not in kwargs:
        kwargs['username'] = get_random_string(length=15)
    password = kwargs.pop('password', 'password')
    user = get_user_model()(**kwargs)
    user.set_password(password)
    if save:
        user.save()
    return user


def email(save=False, **kwargs):
    if 'user' not in kwargs:
        kwargs['user'] = user(save=True)
    if 'email' not in kwargs:
        kwargs['email'] = '%s@%s.com' % (get_random_string(),
                                         get_random_string())
    email = EmailAddress(**kwargs)
    if save:
        email.save()
    return email

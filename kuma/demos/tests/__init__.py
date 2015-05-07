import datetime

from django.contrib.auth import get_user_model

from ..models import Submission


def make_users():
    User = get_user_model()
    user = User.objects.create_user(
        'tester', 'tester@tester.com', 'tester')
    admin_user = User.objects.create_superuser(
        'admin_tester', 'admin_tester@tester.com', 'admint_tester')
    other_user = User.objects.create_user(
        'visitor', 'visitor@visitor.com', 'visitor')
    return (user, admin_user, other_user)


def build_submission(creator):
    now = str(datetime.datetime.now())

    s = Submission(title='Hello world' + now, slug='hello-world' + now,
                   description='This is a hello world demo', hidden=False,
                   creator=creator)
    s.save()

    return s


def build_hidden_submission(creator, slug='hidden-world'):
    now = str(datetime.datetime.now())

    s = Submission(title='Hidden submission 1' + now, slug=slug + now,
                   description='This is a hidden demo', hidden=True,
                   creator=creator)
    s.save()

    return s

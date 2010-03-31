from datetime import datetime

from django.contrib.auth.models import User

from .models import TikiUser


def create_django_user(tiki_user):
    """Make a django.contrib.auth.User for this TikiUser."""
    user = User(id=tiki_user.userId)
    user.username = tiki_user.login
    user.email = tiki_user.email
    user.password = tiki_user.password
    user.date_joined = \
        datetime.fromtimestamp(tiki_user.registrationDate).isoformat(' ')

    user.save()
    return user


class SessionBackend:

    def authenticate(self, session):
        """
        Authenticate using a Tiki Session object
        """

        username = session.user

        try:
            tiki_user = TikiUser.objects.get(login=username)
            user = User.objects.get(pk=tiki_user.userId)
        except User.DoesNotExist:
            user = create_django_user(tiki_user)
        except TikiUser.DoesNotExist:
            session.delete()
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

from django.contrib.auth.models import User

from dekicompat.backends import DekiUser
from devmo.models import UserProfile

def create_profile():
    """Create a user, deki_user, and a profile for a test account"""
    user = User.objects.create_user('tester23', 'tester23@example.com',
                                    'trustno1')

    deki_user = DekiUser(id=0, username='tester23',
                         fullname='Tester Twentythree',
                         email='tester23@example.com',
                         gravatar='', profile_url=None)

    profile = UserProfile()
    profile.user = user
    profile.fullname = "Tester Twentythree"
    profile.title = "Spaceship Pilot"
    profile.organization = "UFO"
    profile.location = "Outer Space"
    profile.bio = "I am a freaky space alien."
    profile.irc_nickname = "ircuser"
    profile.locale = 'en-US'
    profile.timezone = 'US/Central'
    profile.save()

    return (user, deki_user, profile)

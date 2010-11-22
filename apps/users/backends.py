import hashlib
import os

from django.contrib.auth import models as auth_models
from django.contrib.auth.backends import ModelBackend


# http://fredericiana.com/2010/10/12/adding-support-for-stronger-password-hashes-to-django/
"""
from future import django_sha256_support

Monkey-patch SHA-256 support into Django's auth system. If Django ticket #5600
ever gets fixed, this can be removed.
"""


def get_hexdigest(algorithm, salt, raw_password):
    """Generate SHA-256 hash."""
    if algorithm == 'sha256':
        return hashlib.sha256(salt + raw_password).hexdigest()
    else:
        return get_hexdigest_old(algorithm, salt, raw_password)
get_hexdigest_old = auth_models.get_hexdigest
auth_models.get_hexdigest = get_hexdigest


def set_password(self, raw_password):
    """Set SHA-256 password."""
    algo = 'sha256'
    salt = os.urandom(5).encode('hex')  # Random, 10-digit (hex) salt.
    hsh = get_hexdigest(algo, salt, raw_password)
    self.password = '$'.join((algo, salt, hsh))
auth_models.User.set_password = set_password


class Sha256Backend(ModelBackend):
    """
    Overriding the Django model backend without changes ensures our
    monkeypatching happens by the time we import auth.
    """
    pass

import base64
import hashlib
import random

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _


def generate_key():
    """Generate a random API key."""
    # 32 * 8 = 256 random bits
    random_bytes = bytes(random.randint(0, 255) for _ in range(32))
    random_hash = hashlib.sha256(random_bytes).digest()
    replacements = [b"rA", b"aZ", b"gQ", b"hH", b"hG", b"aR", b"DD"]
    random_repl = random.choice(replacements)
    return base64.b64encode(random_hash, random_repl).rstrip(b"=").decode()


def hash_secret(secret):
    return hashlib.sha512((settings.SECRET_KEY + secret).encode()).hexdigest()


class Key(models.Model):
    """Authentication key"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        editable=False,
        db_index=True,
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    key = models.CharField(
        _("Lookup key"), max_length=64, editable=False, db_index=True
    )
    hashed_secret = models.CharField(
        _("Hashed secret"), max_length=128, editable=False, db_index=False
    )
    description = models.TextField(_("Description of intended use"), blank=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"<Key {self.user} {self.key}>"

    def generate_secret(self):
        self.key = generate_key()
        secret = generate_key()
        self.hashed_secret = hash_secret(secret)
        return secret

    def check_secret(self, secret):
        if not self.hashed_secret:
            return False
        return constant_time_compare(hash_secret(secret), self.hashed_secret)

    def log(self, action, content_object=None, notes=None):
        action = KeyAction(
            key=self, action=action, content_object=content_object, notes=notes
        )
        action.save()
        return action


class KeyAction(models.Model):
    """Record of an action taken while using a key"""

    key = models.ForeignKey(
        Key, related_name="history", db_index=True, on_delete=models.CASCADE
    )
    action = models.CharField(max_length=128, blank=False)
    notes = models.TextField(null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created = models.DateTimeField(auto_now_add=True)

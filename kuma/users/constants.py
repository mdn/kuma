import re

from django.utils.translation import gettext_lazy as _


USERNAME_CHARACTERS = _(
    "Username may contain only letters, numbers, and " "these characters: . - _ +"
)
USERNAME_REGEX = re.compile(r"^[\w.+-]+$")
USERNAME_LEGACY_REGEX = re.compile(r"^.+$")

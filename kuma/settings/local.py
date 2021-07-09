from .common import *

# Settings for Docker Development

INTERNAL_IPS = ("127.0.0.1",)

# Default DEBUG to True, and recompute derived settings
DEBUG = config("DEBUG", default=True, cast=bool)
DEBUG_PROPAGATE_EXCEPTIONS = config(
    "DEBUG_PROPAGATE_EXCEPTIONS", default=DEBUG, cast=bool
)

PROTOCOL = config("PROTOCOL", default="https://")
DOMAIN = config("DOMAIN", default="developer-local.allizom.org")
SITE_URL = config("SITE_URL", default=PROTOCOL + DOMAIN)

from django.conf import settings
from django.core.checks import Error, Warning


MISSING_OIDC_RP_CLIENT_ID_ERROR = "kuma.core.E001"
MISSING_OIDC_RP_CLIENT_SECRET_ERROR = "kuma.core.E002"


def oidc_config_check(app_configs, **kwargs):
    errors = []

    for id, key in (
        (MISSING_OIDC_RP_CLIENT_ID_ERROR, "OIDC_RP_CLIENT_ID"),
        (MISSING_OIDC_RP_CLIENT_SECRET_ERROR, "OIDC_RP_CLIENT_SECRET"),
    ):
        if not getattr(settings, key, None):
            class_ = Warning if settings.DEBUG else Error
            errors.append(
                class_(
                    f"{key} environment variable is not set or is empty",
                    id=id,
                )
            )

    # XXX Perhaps, if they *are* set we can open something
    # like https://accounts.firefox.com/.well-known/openid-configuration
    # read the JSON and compare that with things like
    # settings.OIDC_OP_TOKEN_ENDPOINT
    # It might not be super useful but at least it checks the
    # OIDC_OP_AUTHORIZATION_ENDPOINT setting for sanity.

    return errors

from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.core.checks import Error, Warning

from kuma.core.utils import requests_retry_session

MISSING_OIDC_RP_CLIENT_ID_ERROR = "kuma.users.E001"
MISSING_OIDC_RP_CLIENT_SECRET_ERROR = "kuma.users.E002"
MISSING_OIDC_CONFIGURATION_ERROR = "kuma.users.E003"


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

    if settings.OIDC_CONFIGURATION_CHECK:
        errors.extend(_get_oidc_configuration_errors(MISSING_OIDC_CONFIGURATION_ERROR))

    return errors


def _get_oidc_configuration_errors(id):
    errors = []

    configuration_url = settings.OIDC_CONFIGURATION_URL
    parsed = urlparse(configuration_url)
    if not parsed.path or parsed.path == "/":
        default_path = "/.well-known/openid-configuration"
        parsed._replace(path=default_path)
        configuration_url = urljoin(configuration_url, default_path)
    response = requests_retry_session().get(configuration_url)
    response.raise_for_status()
    openid_configuration = response.json()

    for key, setting_key in (
        ("userinfo_endpoint", "OIDC_OP_USER_ENDPOINT"),
        ("authorization_endpoint", "OIDC_OP_AUTHORIZATION_ENDPOINT"),
        ("token_endpoint", "OIDC_OP_TOKEN_ENDPOINT"),
    ):
        setting_value = getattr(settings, setting_key, None)
        if key not in openid_configuration and setting_value:
            errors.append(
                Warning(
                    f"{setting_key} is set but {key!r} is not exposed in {configuration_url}",
                    id=id,
                )
            )
            continue
        config_value = openid_configuration[key]
        if setting_value and config_value != setting_value:
            errors.append(
                Error(
                    f"{setting_key}'s value is different from that on {configuration_url}"
                    f" ({setting_value!r} != {config_value!r}",
                    id=id,
                )
            )

    # ##TODO 14/02/22 - The additional profile:subscriptions scope is currently missing from the supportes scopes in oidc config
    # 
    # settings.OIDC_RP_SCOPES can have less but not more that what's supported
    # scopes_requested = set(settings.OIDC_RP_SCOPES.split())
    # scopes_supported = set(openid_configuration["scopes_supported"])
    # if scopes_supported - scopes_requested:
    #     errors.append(
    #         Error(
    #             f"Invalid settings.OIDC_RP_SCOPES ({settings.OIDC_RP_SCOPES!r}). "
    #             f"Requested: {scopes_requested}, Supported: {scopes_supported}",
    #             id=id,
    #         )
    #     )

    if settings.OIDC_RP_SIGN_ALGO not in set(
        openid_configuration["id_token_signing_alg_values_supported"]
    ):
        errors.append(
            Error(
                f"Invalid settings.OIDC_RP_SIGN_ALGO. "
                f"{settings.OIDC_RP_SIGN_ALGO!r} not in "
                f'{openid_configuration["id_token_signing_alg_values_supported"]}',
                id=id,
            )
        )

    return errors

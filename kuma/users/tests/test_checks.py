from kuma.users.checks import (
    MISSING_OIDC_CONFIGURATION_ERROR,
    MISSING_OIDC_RP_CLIENT_ID_ERROR,
    MISSING_OIDC_RP_CLIENT_SECRET_ERROR,
    oidc_config_check,
)


def test_happy_path_config_check(mock_requests, settings):
    mock_requests.register_uri(
        "GET",
        settings.OIDC_CONFIGURATION_URL + "/.well-known/openid-configuration",
        json={
            "scopes_supported": settings.OIDC_RP_SCOPES.split(),
            "id_token_signing_alg_values_supported": [settings.OIDC_RP_SIGN_ALGO],
            "authorization_endpoint": settings.OIDC_OP_AUTHORIZATION_ENDPOINT,
            "userinfo_endpoint": settings.OIDC_OP_USER_ENDPOINT,
            "token_endpoint": settings.OIDC_OP_TOKEN_ENDPOINT,
        },
    )

    errors = oidc_config_check(None)
    assert not errors


def test_disable_checks(settings):
    # Note! No mock_requests in this test
    settings.OIDC_CONFIGURATION_CHECK = False
    errors = oidc_config_check(None)
    assert not errors


def test_not_happy_path_config_check(mock_requests, settings):
    settings.OIDC_CONFIGURATION_URL += "/"
    mock_requests.register_uri(
        "GET",
        settings.OIDC_CONFIGURATION_URL + ".well-known/openid-configuration",
        json={
            "scopes_supported": ["foo"],
            "id_token_signing_alg_values_supported": ["XXX"],
            "authorization_endpoint": "authorization?",
            "token_endpoint": "token?",
        },
    )

    errors = oidc_config_check(None)
    assert errors
    assert len(errors) == 5
    ids = [error.id for error in errors]
    assert ids == [MISSING_OIDC_CONFIGURATION_ERROR] * len(errors)


def test_missing_important_rp_client_credentials(mock_requests, settings):
    settings.OIDC_CONFIGURATION_URL += "/.well-known/openid-configuration"
    mock_requests.register_uri(
        "GET",
        settings.OIDC_CONFIGURATION_URL,
        json={
            "scopes_supported": settings.OIDC_RP_SCOPES.split(),
            "id_token_signing_alg_values_supported": [settings.OIDC_RP_SIGN_ALGO],
            "authorization_endpoint": settings.OIDC_OP_AUTHORIZATION_ENDPOINT,
            "userinfo_endpoint": settings.OIDC_OP_USER_ENDPOINT,
            "token_endpoint": settings.OIDC_OP_TOKEN_ENDPOINT,
        },
    )

    settings.OIDC_RP_CLIENT_ID = None
    settings.OIDC_RP_CLIENT_SECRET = ""

    errors = oidc_config_check(None)
    assert errors
    ids = [error.id for error in errors]
    assert ids == [MISSING_OIDC_RP_CLIENT_ID_ERROR, MISSING_OIDC_RP_CLIENT_SECRET_ERROR]

from typing import Literal, Optional, Union

from django.conf import settings
from django.middleware.csrf import get_token
from ninja import Router, Schema

from kuma.api.v1.auth import profile_auth
from kuma.api.v1.forms import AccountSettingsForm
from kuma.api.v1.plus.notifications import Ok
from kuma.users.models import UserProfile

from .api import api

settings_router = Router(auth=profile_auth, tags=["settings"])


class AnonResponse(Schema):
    geo: Optional[dict]


class AuthResponse(AnonResponse):
    username: str
    is_authenticated: bool = True
    email: str
    is_staff: Optional[bool]
    is_superuser: Optional[bool]
    avatar_url: Optional[str]
    is_subscriber: Optional[bool]


@api.get(
    "/whoami",
    auth=None,
    exclude_none=True,
    response=Union[AuthResponse, AnonResponse],
    url_name="whoami",
)
def whoami(request):
    """
    Return a JSON object representing the current user, either
    authenticated or anonymous.
    """
    data = {}
    user = request.user
    cloudfront_country_header = "HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME"
    cloudfront_country_value = request.META.get(cloudfront_country_header)
    if cloudfront_country_value:
        data["geo"] = {"country": cloudfront_country_value}

    if not user.is_authenticated:
        return data

    data = {
        "username": user.username,
        "is_authenticated": True,
        "email": user.email,
    }

    if user.is_staff:
        data["is_staff"] = True
    if user.is_superuser:
        data["is_superuser"] = True

    profile = UserProfile.objects.filter(user=user).first()
    if profile:
        data["avatar_url"] = profile.avatar
        data["is_subscriber"] = profile.is_subscriber
    return data


@settings_router.delete("")
def delete_user(request):
    request.user.delete()
    return {"deleted": True}


@settings_router.get("", url_name="settings")
def account_settings(request):
    user_profile: UserProfile = request.auth
    return {
        "csrfmiddlewaretoken": get_token(request),
        "locale": user_profile.locale if user_profile.pk else None,
    }


class FormErrors(Schema):
    ok: Literal[False] = False
    errors: dict[str, list[dict[str, str]]]


@settings_router.post("", response={200: Ok, 400: FormErrors})
def save_settings(request):
    user_profile: UserProfile = request.auth

    form = AccountSettingsForm(request.POST)
    if not form.is_valid():
        return 400, {"errors": form.errors.get_json_data()}

    set_locale = None
    if form.cleaned_data.get("locale"):
        user_profile.locale = form.cleaned_data["locale"]
        user_profile.save()

        response = api.create_response(request, Ok.from_orm(True))
        response.set_cookie(
            key=settings.LANGUAGE_COOKIE_NAME,
            value=set_locale,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
        )
        return response

    return True

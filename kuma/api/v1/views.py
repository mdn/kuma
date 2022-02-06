from typing import Optional, Union
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from ninja import Router, Schema
from ninja.security import django_auth

from kuma.api.v1.forms import AccountSettingsForm
from kuma.api.v1.plus.notifications import Ok
from kuma.users.models import UserProfile

from .api import api

settings_router = Router(auth=django_auth)


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
    "/whoami", auth=None, exclude_none=True, response=Union[AuthResponse, AnonResponse]
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
    return {'deleted': True}


@settings_router.post('', response=Ok)
def save_settings(request):
    user_profile = UserProfile.objects.filter(user=request.user).first()

    form = AccountSettingsForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": form.errors.get_json_data()}, status=400)

    set_locale = None
    if form.cleaned_data.get("locale"):
        set_locale = form.cleaned_data["locale"]
        if user_profile:
            user_profile.locale = set_locale
            user_profile.save()
        else:
            user_profile = UserProfile.objects.create(user=user, locale=set_locale)
    if set_locale:
        response.set_cookie(
            key=settings.LANGUAGE_COOKIE_NAME,
            value=set_locale,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
        )

    return True



@settings_router.get("")
def account_settings(request):
    user = request.user

    user_profile = UserProfile.objects.filter(user=user).first()

    elif request.method == "POST":
        form = AccountSettingsForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

        set_locale = None
        if form.cleaned_data.get("locale"):
            set_locale = form.cleaned_data["locale"]
            if user_profile:
                user_profile.locale = set_locale
                user_profile.save()
            else:
                user_profile = UserProfile.objects.create(user=user, locale=set_locale)

        response = JsonResponse({"ok": True})
        if set_locale:
            response.set_cookie(
                key=settings.LANGUAGE_COOKIE_NAME,
                value=set_locale,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
            )

        return response

    context = {
        "csrfmiddlewaretoken": get_token(request),
        "locale": user_profile.locale if user_profile else None,
    }
    return JsonResponse(context)


api.add_router("/settings", settings_router)

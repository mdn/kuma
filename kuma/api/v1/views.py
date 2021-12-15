from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from kuma.api.v1.forms import AccountSettingsForm
from kuma.users.models import UserProfile


@never_cache
@require_GET
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
        data.update({"geo": {"country": cloudfront_country_value}})

    if not user.is_authenticated:
        return JsonResponse(data)

    data = {
        "username": user.username,
        "is_authenticated": True,
        "email": user.email,
    }

    if user.is_staff:
        data["is_staff"] = True
    if user.is_superuser:
        data["is_superuser"] = True
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = None

    if profile:
        data["avatar_url"] = profile.avatar
        if profile.is_subscriber:
            data["is_subscriber"] = True
    return JsonResponse(data)


@never_cache
def account_settings(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("not signed in")

    for user_profile in UserProfile.objects.filter(user=user):
        break
    else:
        user_profile = None

    if request.method == "DELETE":
        user.delete()
        return JsonResponse({"deleted": True})
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

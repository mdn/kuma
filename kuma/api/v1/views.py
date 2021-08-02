from django.conf import settings
from django.http import (
    HttpResponseForbidden,
    JsonResponse,
)
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
    user = request.user
    if user.is_authenticated:
        data = {
            "username": user.username,
            "is_authenticated": True,
            "email": user.email,
        }

        if user.is_staff:
            data["is_staff"] = True
        if user.is_superuser:
            data["is_superuser"] = True
        for user_profile_claims in UserProfile.objects.filter(user=user).values_list(
            "claims", flat=True
        ):
            # 'avatarDefault' is set to truthy if the user doesn't have an avatar.
            # If it's the case, the user simply hasn't uploaded an avatar. And
            # FxA will still send a default avatar which is usually just a
            # a picture of the initial letter of the email.
            if user_profile_claims.get("avatar") and not user_profile_claims.get(
                "avatarDefault"
            ):
                data["avatar_url"] = user_profile_claims["avatar"]

            # XXX would be nice to use the profile to set:
            # data['subscriber_number'] = ...
            # data['is_subscriber'] = ...

    else:
        data = {}

    geo = {}
    # https://aws.amazon.com/about-aws/whats-new/2020/07/cloudfront-geolocation-headers/
    cloudfront_country_header = "HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME"
    cloudfront_country_value = request.META.get(cloudfront_country_header)
    if cloudfront_country_value:
        geo["country"] = cloudfront_country_value
    if geo:
        data["geo"] = geo

    return JsonResponse(data)


@never_cache
def account_settings(request):
    user = request.user
    for user_profile in UserProfile.objects.filter(user=user):
        break
    else:
        user_profile = None

    if not user.is_authenticated:
        return HttpResponseForbidden("not signed in")
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
        "locale": user_profile and user_profile.locale or None,
        # "subscription": user.stripe_customer_id
        # and retrieve_and_synchronize_stripe_subscription(user)
        # or None,
    }
    return JsonResponse(context)

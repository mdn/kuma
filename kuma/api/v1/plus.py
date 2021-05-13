import json
from uuid import UUID

from django.http import HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from ratelimit.decorators import ratelimit

from kuma.plus.models import LandingPageSurvey


@ratelimit(key="user_or_ip", rate="100/m", block=True)
@require_http_methods(["GET", "POST"])
def landing_page_survey(request):
    context = {}
    if request.method == "POST":
        uuid = request.POST.get("uuid")
        if not uuid:
            return HttpResponseBadRequest("missing 'uuid'")
        survey = get_object_or_404(LandingPageSurvey, uuid=uuid)
        email = request.POST.get("email")
        if email:
            survey.email = email.strip()
            survey.save()

        response_json = request.POST.get("response")
        if response_json:
            try:
                response = json.loads(response_json)
            except ValueError:
                return HttpResponseBadRequest("invalid response JSON")
            survey.response = json.dumps(response)
            survey.save()
        context["ok"] = True
    else:
        variant = request.GET.get("variant")
        if not variant:
            return HttpResponseBadRequest("missing 'variant'")
        try:
            variant = int(variant)
        except ValueError:
            return HttpResponseBadRequest("invalid 'variant'")
        uuid = request.GET.get("uuid")
        if uuid:
            try:
                UUID(uuid)
            except ValueError:
                return HttpResponseBadRequest("invalid 'uuid'")
            survey = get_object_or_404(LandingPageSurvey, uuid=uuid)
        else:
            # Inspired by https://github.com/mdn/kuma/pull/7849/files
            geo_information = (
                request.META.get("HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME") or ""
            )
            survey = LandingPageSurvey.objects.create(
                variant=variant,
                geo_information=geo_information,
                user=request.user if request.user.is_authenticated else None,
            )
        context["uuid"] = survey.uuid
        context["csrfmiddlewaretoken"] = get_token(request)

    return JsonResponse(context)

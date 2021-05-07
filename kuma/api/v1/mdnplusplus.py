import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from ratelimit.decorators import ratelimit

from kuma.mdnplusplus.models import LandingPageSurvey


@ratelimit(key="user_or_ip", rate="10/m", block=True)
@require_http_methods(["GET", "POST"])
def landing_page_survey(request):
    context = {}
    if request.method == "POST":
        variant = request.POST.get("variant")
        if not variant:
            return HttpResponseBadRequest("missing 'variant'")
        uuid = request.POST.get("variant")
        if not uuid:
            return HttpResponseBadRequest("missing 'uuid'")
        survey = get_object_or_404(LandingPageSurvey, uuid=request.POST.get("uuid"))
        if request.POST.get("email"):
            survey.email = request.POST.get("email").strip()
            survey.save()
        if request.POST.get("response"):
            try:
                response = json.loads(request.POST.get("response"))
            except ValueError:
                return HttpResponseBadRequest("invalid response JSON")
            survey.response = json.dumps(response)
            survey.save()
        context["ok"] = True
    else:
        variant = request.GET.get("variant")
        if not variant:
            return HttpResponseBadRequest("missing 'variant'")
        if request.GET.get("uuid"):
            survey = get_object_or_404(LandingPageSurvey, uuid=request.GET.get("uuid"))
        else:
            # Ryan said it was called 'CloudFront-Viewer-Country'
            # but https://aws.amazon.com/about-aws/whats-new/2020/07/cloudfront-geolocation-headers/
            # says it's called 'CloudFront-Viewer-Country-Name'
            geo_information = request.META.get(
                "CloudFront-Viewer-Country"
            ) or request.META.get("CloudFront-Viewer-Country-Name")
            survey = LandingPageSurvey.objects.create(
                variant=variant, geo_information=geo_information
            )
        context["uuid"] = survey.uuid

    return JsonResponse(context)

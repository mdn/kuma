from uuid import UUID

from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import Json
from ratelimit.decorators import ratelimit

from kuma.api.v1.plus.notifications import Ok
from kuma.api.v1.smarter_schema import Schema
from kuma.plus.models import LandingPageSurvey

api = Router()


class SurveySchema(Schema):
    uuid: UUID
    response: Json


@api.post("/survey/", response=Ok)
@ratelimit(group="landing_page_survey", key="user_or_ip", rate="100/m", block=True)
def post_survey(request, body: SurveySchema):
    survey = get_object_or_404(LandingPageSurvey, uuid=body.uuid)
    survey.response = body.response
    survey.save()
    return True


@api.get("/survey/")
@ratelimit(group="landing_page_survey", key="user_or_ip", rate="100/m", block=True)
def get_survey(request, uuid: UUID = None):
    # Inspired by https://github.com/mdn/kuma/pull/7849/files
    if uuid:
        survey = get_object_or_404(LandingPageSurvey, uuid=uuid)
    else:
        geo_information = request.META.get("HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME") or ""
        survey = LandingPageSurvey.objects.create(
            geo_information=geo_information,
        )
    return {"uuid": survey.uuid, "csrfmiddlewaretoken": get_token(request)}

from uuid import uuid4

from django.db import models


class LandingPageSurvey(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    # An insecure random string so that when a survey is submitted with more information
    # it can not easily be guessed and the ratelimit will make it impossible to try
    # all combinations.
    response = models.JSONField(editable=False, null=True)
    geo_information = models.TextField(editable=False, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.uuid)

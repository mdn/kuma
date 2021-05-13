from uuid import uuid4

from django.conf import settings
from django.db import models


class LandingPageSurvey(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    # An insecure random string so that when a survey is submitted with more information
    # it can not easily be guessed and the ratelimit will make it impossible to try
    # all combinations.
    email = models.CharField(max_length=100, blank=True)
    variant = models.PositiveIntegerField()
    # Wish we had a proper JSON model but this is MySQL and Django 2.
    response = models.TextField(editable=False, null=True)
    geo_information = models.TextField(editable=False, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.uuid)

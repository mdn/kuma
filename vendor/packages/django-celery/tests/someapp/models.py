from django.db import models  # noqa


class Thing(models.Model):
    name = models.CharField(max_length=10)

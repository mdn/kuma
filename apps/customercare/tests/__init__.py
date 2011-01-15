from datetime import datetime
import random

from django.conf import settings

from customercare import models


def cc_category(save=True, **kwargs):
    """Return a canned category."""
    responses = kwargs.pop('responses', [])
    save = save or responses  # Adding responses forces save.
    defaults = {'title': str(datetime.now()),
                'weight': random.choice(range(50)),
                'locale': settings.LANGUAGE_CODE}
    defaults.update(kwargs)

    category = models.CannedCategory(**defaults)
    if save:
        category.save()
    # Add responses to this category.
    for response, weight in responses:
        models.CategoryMembership.objects.create(
            category=category, response=response, weight=weight)

    return category


def cc_response(save=True, **kwargs):
    """Return a canned response."""
    categories = kwargs.pop('categories', [])
    save = save or categories  # Adding categories forces save.

    defaults = {'title': str(datetime.now()),
                'response': 'Test response (%s).' % random.choice(range(50)),
                'locale': settings.LANGUAGE_CODE}
    defaults.update(kwargs)

    response = models.CannedResponse(**defaults)
    if save:
        response.save()
    # Add categories to this response.
    for category, weight in categories:
        weight = random.choice(range(50))
        models.CategoryMembership.objects.create(
            category=category, response=response, weight=weight)

    return response

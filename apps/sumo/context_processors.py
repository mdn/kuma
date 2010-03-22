from django.conf import settings


def title(request):
    """
    Adds site title to the context.

    """
    return {'SITE_TITLE': settings.SITE_TITLE}

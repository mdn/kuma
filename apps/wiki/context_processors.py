from django.conf import settings

from constance import config

from .models import Document


def custom_css(request):
    custom_css = ''
    try:
        custom_css_doc = Document.objects.get(slug=config.KUMA_CUSTOM_CSS_DOC,
                                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        custom_css = custom_css_doc.html
    except Document.DoesNotExist:
        # If it doesn't exist, return ''
        pass
    return {'KUMA_CUSTOM_CSS': custom_css}

from django.conf import settings
from django.shortcuts import render


def index(request):
    # settings.SORTED_LANGUAGES is used by the select drop down
    # on the account settings landing page
    sorted_languages = dict(settings.SORTED_LANGUAGES)
    return render(
        request, "accountsettings/index.html", {"sorted_languages": sorted_languages}
    )

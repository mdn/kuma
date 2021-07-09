from django.http import HttpResponse

from kuma.core.decorators import shared_cache_control


@shared_cache_control(s_maxage=60 * 60 * 24 * 30)
def humans_txt(request):
    """We no longer maintain an actual /humans.txt endpoint but to avoid the
    sad 404 we instead now just encourage people to go and use the GitHub
    UI to see the contributors."""
    return HttpResponse("See https://github.com/mdn/kuma/graphs/contributors\n")

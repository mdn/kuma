from .jobs import CommandFiltersJob


def search_filters(request):
    if hasattr(request, 'path') and request.path.startswith('/search'):
        return

    return CommandFiltersJob().get()

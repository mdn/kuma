from django.shortcuts import render


def handle403(request):
    """A 403 message that looks nicer than the normal Apache forbidden page."""

    return render(request, 'handlers/403.html', status=403)

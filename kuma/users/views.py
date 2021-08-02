def logout_url(request):
    """This gets called by mozilla_django_oidc when a user has signed out."""
    print("next?", request.GET.get("next"))
    return "/"

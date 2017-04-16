# based on django.contrib.admin.__init__.py

from django.utils.importlib import import_module
LOADING = False

from django.conf import settings
REGISTRATION_MODULE_NAME = getattr(
    settings, 'DBGETTEXT_REGISTRATION_MODULE_NAME', 'dbgettext_registration')

def autodiscover():
    """
    Auto-discover INSTALLED_APPS dbgettext_registration.py modules and fail 
    silently when not present. This forces an import on them to register any 
    dbggettext bits they may want.
    """
    global LOADING
    if LOADING:
        return
    LOADING = True

    import imp
    for app in settings.INSTALLED_APPS:
        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue

        try:
            imp.find_module(REGISTRATION_MODULE_NAME, app_path)
        except ImportError:
            continue

        import_module("%s.%s" % (app, REGISTRATION_MODULE_NAME))
    
    # import project-level options
    if hasattr(settings, 'DBGETTEXT_PROJECT_OPTIONS'):
        import_module(settings.DBGETTEXT_PROJECT_OPTIONS)

    LOADING = False

# go:
autodiscover()

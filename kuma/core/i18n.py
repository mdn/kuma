from django.apps import apps


def get_language_mapping():
    return apps.get_app_config('core').language_mapping

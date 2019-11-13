import json
import os
from json.decoder import JSONDecodeError

from django.conf import settings
from django.core.checks import Error, register as register_check, Warning


WARNING_MISSING_I18N_DATA = 'kuma.core.W001'
ERROR_MISSING_I18N_FILE = 'kuma.core.E001'
ERROR_CORRUPT_I18N_FILE = 'kuma.core.E002'


def react_i18n_check(app_configs, **kwargs):
    """For every settings.ACCEPTED_LOCALES there's supposed to be one
    i18n file prepared.
    This makes sure you have run `make compilejsi18n` and
    `make compile-react-i18n` before starting Django.
    """
    errors = []

    # Use this long for so humans can copy and paste it directly.
    general_hint = "Run 'docker-compose exec web make build-static'"

    for locale in settings.ACCEPTED_LOCALES:
        path = os.path.join(
            settings.BASE_DIR, 'static', 'jsi18n', locale, 'react.json')
        try:
            with open(path) as f:
                try:
                    data = json.load(f)
                except JSONDecodeError as exception:
                    errors.append(Error(
                        'Locale file {} is corrupt ({})'.format(
                            path, exception
                        ),
                        hint=general_hint,
                        id=ERROR_CORRUPT_I18N_FILE,
                    ))
                    continue

                missing = [
                    key for key in ('catalog', 'plural', 'formats')
                    if key not in data
                ]
                if missing:
                    errors.append(Warning(
                        'Locale file {} is missing keys {!r}'.format(
                            path, missing
                        ),
                        hint=general_hint,
                        id=WARNING_MISSING_I18N_DATA,
                    ))
        except FileNotFoundError:
            errors.append(Error(
                'Locale file {} does not exist'.format(path),
                hint=general_hint,
                id=ERROR_MISSING_I18N_FILE,
            ))
    return errors


def register():
    register_check(react_i18n_check)

import json
import os

from django.core.checks import Error, Warning

from kuma.core import checks


def test_react_i18n_check(tmpdir, settings):
    settings.ACCEPTED_LOCALES = ['sv-SE', 'en-US']
    settings.BASE_DIR = base_dir = str(tmpdir)
    os.makedirs(os.path.join(base_dir, 'static', 'jsi18n', 'sv-SE'))
    os.makedirs(os.path.join(base_dir, 'static', 'jsi18n', 'en-US'))

    # Because we'll reuse this a lot
    general_hint = "Run 'make compile-react-i18n'"

    # Missing the react.json files
    errors = checks.react_i18n_check(None)
    assert len(errors) == 2
    sv_path = os.path.join(base_dir, 'static', 'jsi18n', 'sv-SE', 'react.json')
    assert errors[0] == Error(
        'Locale file {} does not exist'.format(sv_path),
        hint=general_hint,
        id=checks.ERROR_MISSING_I18N_FILE
    )
    # Create both but make one of them weird
    en_path = os.path.join(base_dir, 'static', 'jsi18n', 'en-US', 'react.json')
    with open(en_path, 'w') as f:
        json.dump({
            "formats": [],
            "catalog": {},
            "plural": "multiple"
        }, f)
    with open(sv_path, 'w') as f:
        f.write('{{not valid JSON')
    errors = checks.react_i18n_check(None)
    assert len(errors) == 1
    # In this test, we can't compare the 'errors[0]' against a whole object
    # because it contains a dynamic string (the JSON decode error form Python).
    assert errors[0].id == checks.ERROR_CORRUPT_I18N_FILE

    # Now mess with the content of the (valid) JSON
    with open(sv_path, 'w') as f:
        json.dump({
            "formats": [],
            "plural": "multiple",
            # Missing 'catalog'
        }, f)
    errors = checks.react_i18n_check(None)
    assert len(errors) == 1
    assert errors[0] == Warning(
        'Locale file {} is missing keys {!r}'.format(sv_path, ['catalog']),
        hint=general_hint,
        id=checks.WARNING_MISSING_I18N_DATA
    )

    # Make it shine of happiness
    with open(sv_path, 'w') as f:
        json.dump({
            "formats": [],
            "plural": "multiple",
            "catalog": {},
        }, f)
    errors = checks.react_i18n_check(None)
    assert not errors

from __future__ import absolute_import, unicode_literals

import warnings

from django.conf import settings
from django.utils import six


# Always import this module as follows:
# from debug_toolbar import settings [as dt_settings]

# Don't import directly CONFIG or PANELs, or you will miss changes performed
# with override_settings in tests.


CONFIG_DEFAULTS = {
    # Toolbar options
    'INSERT_BEFORE': '</body>',
    'RENDER_PANELS': None,
    'RESULTS_STORE_SIZE': 10,
    'ROOT_TAG_EXTRA_ATTRS': '',
    'SHOW_COLLAPSED': False,
    'SHOW_TOOLBAR_CALLBACK': 'debug_toolbar.middleware.show_toolbar',
    # Panel options
    'EXTRA_SIGNALS': [],
    'ENABLE_STACKTRACES': True,
    'HIDE_IN_STACKTRACES': (
        'socketserver' if six.PY3 else 'SocketServer',
        'threading',
        'wsgiref',
        'debug_toolbar',
        'django',
    ),
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TEMPLATE_CONTEXT': True,
    'SQL_WARNING_THRESHOLD': 500,   # milliseconds
}

USER_CONFIG = getattr(settings, 'DEBUG_TOOLBAR_CONFIG', {})
# Backward-compatibility for 1.0, remove in 2.0.
_RENAMED_CONFIG = {
    'RESULTS_STORE_SIZE': 'RESULTS_CACHE_SIZE',
    'ROOT_TAG_ATTRS': 'ROOT_TAG_EXTRA_ATTRS',
    'HIDDEN_STACKTRACE_MODULES': 'HIDE_IN_STACKTRACES'
}
for old_name, new_name in _RENAMED_CONFIG.items():
    if old_name in USER_CONFIG:
        warnings.warn(
            "%r was renamed to %r. Update your DEBUG_TOOLBAR_CONFIG "
            "setting." % (old_name, new_name), DeprecationWarning)
        USER_CONFIG[new_name] = USER_CONFIG.pop(old_name)
if 'HIDE_DJANGO_SQL' in USER_CONFIG:
    warnings.warn(
        "HIDE_DJANGO_SQL was removed. Update your "
        "DEBUG_TOOLBAR_CONFIG setting.", DeprecationWarning)
    USER_CONFIG.pop('HIDE_DJANGO_SQL')
if 'TAG' in USER_CONFIG:
    warnings.warn(
        "TAG was replaced by INSERT_BEFORE. Update your "
        "DEBUG_TOOLBAR_CONFIG setting.", DeprecationWarning)
    USER_CONFIG['INSERT_BEFORE'] = '</%s>' % USER_CONFIG.pop('TAG')

CONFIG = CONFIG_DEFAULTS.copy()
CONFIG.update(USER_CONFIG)
if not isinstance(CONFIG['SHOW_TOOLBAR_CALLBACK'], six.string_types):
    warnings.warn(
        "SHOW_TOOLBAR_CALLBACK is now a dotted path. Update your "
        "DEBUG_TOOLBAR_CONFIG setting.", DeprecationWarning)


PANELS_DEFAULTS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

try:
    PANELS = list(settings.DEBUG_TOOLBAR_PANELS)
except AttributeError:
    PANELS = PANELS_DEFAULTS
else:
    # Backward-compatibility for 1.0, remove in 2.0.
    _RENAMED_PANELS = {
        'debug_toolbar.panels.version.VersionDebugPanel':
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel':
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings_vars.SettingsDebugPanel':
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel':
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel':
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel':
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel':
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CacheDebugPanel':
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalDebugPanel':
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logger.LoggingDebugPanel':
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.InterceptRedirectsDebugPanel':
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingDebugPanel':
        'debug_toolbar.panels.profiling.ProfilingPanel',
    }
    for index, old_panel in enumerate(PANELS):
        new_panel = _RENAMED_PANELS.get(old_panel)
        if new_panel is not None:
            warnings.warn(
                "%r was renamed to %r. Update your DEBUG_TOOLBAR_PANELS "
                "setting." % (old_panel, new_panel), DeprecationWarning)
            PANELS[index] = new_panel


PATCH_SETTINGS = getattr(settings, 'DEBUG_TOOLBAR_PATCH_SETTINGS', settings.DEBUG)

import os
import site

# Add the kitsune dir to the python path so we can import manage which sets up
# other paths and settings.
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../')))

# We let Apache tell us where to find site packages through the SITE variable
# in the wsgi environment. That means we can't import anything from django or
# kitsune until we're inside of a request, so the first time through will run
# basic imports and validates our models (which cascades to import
# <apps>.models).


class KitsuneApp:

    def __init__(self):
        self.setup = False

    def __call__(self, env, start_response):
        if not self.setup:
            self.setup_app(env)
            self.setup = True
        return self.kitsune_app(env, start_response)

    def setup_app(self, env):
        if 'SITE' in env:
            site.addsitedir(env['SITE'])

        # manage adds the `apps` and `lib` directories to the path.
        import manage

        import django.conf
        import django.core.handlers.wsgi
        import django.core.management
        import django.utils

        # Do validate and activate translations like using
        # `./manage.py runserver`
        # http://blog.dscpl.com/au/2010/03/improved-wsgi-script-for-use-with.html
        utility = django.core.management.ManagementUtility()
        command = utility.fetch_command('runserver')
        command.validate()
        django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)

        # This is what mod_wsgi runs.
        self.wsgi_handler = django.core.handlers.wsgi.WSGIHandler()

    def kitsune_app(self, env, start_response):
        if 'HTTP_X_ZEUS_DL_PT' in env:
            env['SCRIPT_URL'] = env['SCRIPT_NAME'] = ''
        return self.wsgi_handler(env, start_response)

application = KitsuneApp()

# Uncomment this to figure out what's going on with the mod_wsgi environment.
# def application(env, start_response):
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     return '\n'.join('%r: %r' % item for item in sorted(env.items()))

# vim: ft=python

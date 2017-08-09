"""
Deployment for MDN

Requires commander (https://github.com/oremj/commander) which is installed on
the systems that need it.
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups  # noqa

import commander_settings as settings  # noqa

VENV_BIN = os.path.join(settings.VENV_DIR, 'bin')
PIP_VERSION = "8.0.2"


# Set local settings to legacy name until we can safely use environment
# specifc one.
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_local'

# Use commander's remote hostname to differ between stage and prod in setting.py
os.environ['CHIEF_REMOTE_HOSTNAME'] = settings.REMOTE_HOSTNAME

# Setup local executable paths
os.environ['PATH'] = os.pathsep.join([
    VENV_BIN,  # python virtualenv executables
    '/usr/local/bin',  # node global executables
    os.environ['PATH']])  # The existing paths


@task
def update_code(ctx, tag):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("git fetch")
        ctx.local("git checkout -f %s" % tag)
        ctx.local("git submodule sync")
        ctx.local("git submodule update --init --recursive")


@task
def update_locales(ctx):
    with ctx.lcd(os.path.join(settings.SRC_DIR, 'locale')):
        ctx.local("dennis-cmd lint --errorsonly .")
        ctx.local("../scripts/compile-mo.sh .")


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.7 manage.py compilejsi18n")
        ctx.local("python2.7 manage.py collectstatic --noinput")


@task
def database(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.7 manage.py migrate --noinput")


@task
def checkin_changes(ctx):
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.KUMA_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_app(ctx):
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)


@hostgroups(settings.KUMA_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def restart_web(ctx):
    ctx.remote("service httpd restart")


@hostgroups(settings.KUMA_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def restart_kumascript(ctx):
    ctx.remote("/usr/bin/supervisorctl stop all; /usr/bin/killall nodejs; /usr/bin/supervisorctl start all")


@hostgroups(settings.CELERY_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def restart_celery(ctx):
    ctx.remote('/usr/bin/supervisorctl mrestart celery\*')


# As far as I can tell, Chief does not pass the username to commander,
# so I can't give a username here: (
# also doesn't pass ref at this point... we have to backdoor that too!
@task
def ping_newrelic(ctx):
    f = open(settings.SRC_DIR + "/media/revision.txt", "r")
    tag = f.read().strip()
    f.close()
    url = ('https://api.newrelic.com/v2/applications/%s/deployments.json' %
           settings.NEWRELIC_APP_ID)
    deployment = {
        'deployment': {
            'revision': tag,
            'user': 'Chief'
        }
    }
    ctx.local(("curl --silent"
               " -X POST '%(URL)s'"
               " -H 'X-Api-Key:%(API_KEY)s'"
               " -H 'Content-Type: application/json'"
               " -d '%(DEPLOYMENT_JSON)s'"
               % {'URL': url,
                  'API_KEY': settings.NEWRELIC_API_KEY,
                  'DEPLOYMENT_JSON': json.dumps(deployment)}))


@task
def update_info(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("date")
        ctx.local("git branch")
        ctx.local("git log -3")
        ctx.local("git status")
        ctx.local("git submodule status")
        ctx.local("python2.7 ./manage.py migrate --list")
        ctx.local("git rev-parse HEAD > media/revision.txt")
    with ctx.lcd(os.path.join(settings.SRC_DIR, 'kumascript')):
        ctx.local("git rev-parse HEAD > ../media/kumascript-revision.txt")


@task
def setup_dependencies(ctx):
    with ctx.lcd(settings.SRC_DIR):
        # Dearly beloved. We gather here to destroy this virtualenv in the
        # hopes that out of the ashes will rise another new and beautiful
        # virtualenv with no mistakes in it.
        ctx.local('rm -rf %s' % settings.VENV_DIR)
        ctx.local('virtualenv-2.7 --no-site-packages %s' % settings.VENV_DIR)

        # Activate virtualenv to append to the correct path to $PATH.
        activate_env = os.path.join(VENV_BIN, 'activate_this.py')
        execfile(activate_env, dict(__file__=activate_env))

        pip = os.path.join(VENV_BIN, 'pip')
        ctx.local('%s install --upgrade "pip==%s"' % (pip, PIP_VERSION))
        ctx.local('pip --version')
        ctx.local('%s install -r requirements/default.txt' % pip)
        # Make the virtualenv relocatable
        ctx.local('virtualenv-2.7 --relocatable %s' % settings.VENV_DIR)

        # Fix lib64 symlink to be relative instead of absolute.
        ctx.local('rm -f %s' % os.path.join(settings.VENV_DIR, 'lib64'))
        with ctx.lcd(settings.VENV_DIR):
            ctx.local('ln -s lib lib64')

    # And now for node.js node_modules
    with ctx.lcd(os.path.join(settings.SRC_DIR, 'kumascript')):
        ctx.local('rm -rf node_modules')
        ctx.local('npm install --production')
        # Update any top-level npm packages listed in package.json,
        # as allowed by each package's given "semver".
        ctx.local('npm update --production')


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    update_code(ref)
    setup_dependencies()
    update_info()
    # if ref == 'name-of-migration-tag':
    #     with ctx.lcd(settings.SRC_DIR):
    #         # run migrations here


@task
def update(ctx):
    update_assets()
    update_locales()
    database()


@task
def deploy(ctx):
    checkin_changes()
    deploy_app()
    restart_web()
    restart_kumascript()
    restart_celery()
    ping_newrelic()


@task
def update_mdn(ctx, tag):
    """Do typical mdn update"""
    pre_update(tag)
    update()

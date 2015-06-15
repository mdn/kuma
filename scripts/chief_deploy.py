"""
Deployment for MDN

Requires commander (https://github.com/oremj/commander) which is installed on
the systems that need it.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups

import commander_settings as settings

# Setup venv path
venv_bin_path = os.path.join(settings.VENV_DIR, 'bin')
os.environ['PATH'] = venv_bin_path + os.pathsep + os.environ['PATH']

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
        ctx.local("svn up")
        ctx.local("./compile-mo.sh .")


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.7 manage.py collectstatic --noinput")
        ctx.local("python2.7 manage.py compilejsi18n")
        ctx.local("./scripts/compile-stylesheets")
        ctx.local("LANG=en_US.UTF-8 python2.7 manage.py compress_assets")


@task
def database(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.7 manage.py migrate --noinput")


@task
def checkin_changes(ctx):
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_app(ctx):
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote("service httpd restart")

@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_kumascript(ctx):
    ctx.remote("/usr/bin/supervisorctl stop all; /usr/bin/killall nodejs; /usr/bin/supervisorctl start all")

@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def prime_app(ctx):
    for http_port in range(80, 82):
        ctx.remote("for i in {1..10}; do curl -so /dev/null -H 'Host: %s' -I http://localhost:%s/ & sleep 1; done" % (settings.REMOTE_HOSTNAME, http_port))

@hostgroups(settings.CELERY_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def update_celery(ctx):
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('/usr/bin/supervisorctl mrestart celery\*')

# As far as I can tell, Chief does not pass the username to commander,
# so I can't give a username here: (
# also doesn't pass ref at this point... we have to backdoor that too!
@task
def ping_newrelic(ctx):
    f = open(settings.SRC_DIR + "/media/revision.txt", "r")
    tag = f.read()
    f.close()
    ctx.local('curl --silent -H "x-api-key:%s" -d "deployment[app_name]=%s" -d "deployment[revision]=%s" -d "deployment[user]=Chief" https://rpm.newrelic.com/deployments.xml' % (settings.NEWRELIC_API_KEY, settings.REMOTE_HOSTNAME, tag))

@task
def update_info(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("date")
        ctx.local("git branch")
        ctx.local("git log -3")
        ctx.local("git status")
        ctx.local("git submodule status")
        ctx.local("python2.7 ./manage.py migrate --list")
        with ctx.lcd("locale"):
            ctx.local("svn info")
            ctx.local("svn status")

        ctx.local("git rev-parse HEAD > media/revision.txt")


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    update_code(ref)
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
    deploy_kumascript()
    ping_newrelic()
#    prime_app()
    update_celery()


@task
def update_mdn(ctx, tag):
    """Do typical mdn update"""
    pre_update(tag)
    update()

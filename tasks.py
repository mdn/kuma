from invoke import run, task

default_name = 'wheels'


@task
def clean(name=default_name):
    run('rm -rf {0} {0}.tar.xz'.format(name))


@task('clean')
def wheels(name=default_name):
    run('sudo pip2.6 wheel --no-use-wheel --wheel-dir={0} '
        '--download-cache=/home/vagrant/src/puppet/cache/pip '
        '-r requirements/prod.txt '
        '-r requirements/dev.txt '
        '-r requirements/compiled.txt'.format(name))
    run('tar cfJ {0}.tar.xz {0} && rm -rf {0}'.format(name))
    print("\n  If you have access to S3 you can run now: 'inv upload'")


@task
def upload(name=default_name):
    run('aws --profile mozilla s3 cp --acl public-read '
        '{0}.tar.xz s3://pkgs.mozilla.net/python/mdn/{0}.tar.xz'.format(name))
    print("\n  Running 'inv clean' is recommended")

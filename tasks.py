import os
from invoke import run, task, Collection

target = 'wheelhouse'
ns = Collection()


def go(cmd, **kwargs):
    return run(cmd.format(**kwargs))


@task
def clean(name):
    go('rm -rf {name}', name=target)


def build_wheelball(name, requirements,
                    cache='/tmp'):
    requirements = ['-r requirements/{0}.txt'.format(req)
                    for req in requirements]

    go('mkdir -p {name}', name=target)
    label = os.path.join(target, name)
    go('sudo pip2.6 wheel --no-use-wheel --wheel-dir={label} {reqs} '
        '--download-cache={cache}',
        label=label, reqs=' '.join(requirements), cache=cache)
    go('cd {target} && tar cfJ {name}.tar.xz {name}',
       target=target, name=name)
    go('cd .. && rm -rf {label}', label=label)
    print('Built ' + label)


@task('clean')
def base_wheels(name='wheels'):
    build_wheelball(name, ['prod', 'dev', 'compiled'])


@task('clean')
def travis_wheels(name='travis_wheels'):
    build_wheelball(name, ['compiled'])


@task
def upload(name):
    go('aws --profile mozilla s3 cp --acl public-read '
       '{name}.tar.xz s3://pkgs.mozilla.net/python/mdn/{name}.tar.xz',
       name=name)


wheel = Collection('wheel')
wheel.add_task(base_wheels, 'base')
wheel.add_task(travis_wheels, 'travis')
ns.add_collection(wheel)
ns.add_task(upload)
ns.add_task(clean)

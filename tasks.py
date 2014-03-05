import os
from invoke import run, task

here = os.path.dirname(__file__)
target = os.path.join(here, 'wheelhouse')
os.environ.setdefault('AWS_CONFIG_FILE', os.path.join(here, '.awsconfig'))


def go(cmd, **kwargs):
    # print cmd, kwargs
    return run(cmd.format(**kwargs))


def build_wheelball(name, requirements,
                    cache='/tmp'):
    print('Started running wheel builder {0}'.format(name))
    requirements = ['-r requirements/{0}.txt'.format(req)
                    for req in requirements]

    go('mkdir -p {name}', name=target)
    label = os.path.join(target, name)
    go('sudo pip2.6 wheel --no-use-wheel --wheel-dir={label} {reqs} '
        '--download-cache={cache}',
        label=label, reqs=' '.join(requirements), cache=cache)
    go('cd {target} && tar cfz {name}.tar.gz {name}',
       target=target, name=name)
    go('cd .. && rm -rf {label}', label=label)
    print('Done running wheel builder {0}. Built {1}.tar.gz'.format(name,
                                                                    label))


wheel_builders = {
    'base': lambda: build_wheelball('base_wheels', ['prod', 'dev', 'compiled']),
    'travis': lambda: build_wheelball('travis_wheels', ['compiled']),
}


@task
def build(only=None):
    if only is None:
        for name, builder in wheel_builders.items():
            builder()
    else:
        builder = wheel_builders.get(only, None)
        if builder:
            builder()


@task
def upload(only=None):
    aws_config = os.environ['AWS_CONFIG_FILE']
    if not os.path.exists(aws_config):
        print('No AWS config file found at {0}'.format(aws_config))
        return
    if only is None:
        names = wheel_builders.keys()
    else:
        names = [only]
    for name in names:
        print('Starting uploading {name} wheel file'.format(name=name))
        path = os.path.join(target, name)
        go('aws --profile mozilla s3 cp --acl public-read '
           '{path}_wheels.tar.gz '
           's3://pkgs.mozilla.net/python/mdn/{name}_wheels.tar.gz',
           path=path, name=name)
        print('Done uploading {name} wheel file'.format(name=name))
    print('You may want to run: rm -rf {target}'.format(target=target))


@task
def install(name):
    tmpdir = os.path.join(here, 'wheelhouse_tmp')
    go('mkdir {tmpdir}', tmpdir=tmpdir)
    go('cd {tmpdir} && curl -LO '
        'https://s3-us-west-2.amazonaws.com/pkgs.mozilla.net/python/mdn/{name}_wheels.tar.gz '
        '-o {name}_wheels.tar.gz',
       name=name, tmpdir=tmpdir)
    go('cd {tmpdir} && tar xvfz {name}_wheels.tar.gz && '
       'rm {name}_wheels.tar.gz', name=name, tmpdir=tmpdir)
    go('sudo pip install --no-index --find-links={tmpdir}/{name}_wheels '
        '-r requirements/prod.txt -r requirements/dev.txt',
        tmpdir=tmpdir, name=name)
    go('rm -rf {tmpdir}', tmpdir=tmpdir)

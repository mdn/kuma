import subprocess
import zlib

from django.conf import settings


crc32 = lambda x: zlib.crc32(x) & 0xffffffff


call = lambda x: subprocess.Popen(x, stdout=subprocess.PIPE).communicate()


def reindex(rotate=False):
    """
    Reindexes sphinx.  Note this is only to be used in dev and test
    environments.
    """
    calls = [settings.SPHINX_INDEXER, '--all', '--config',
             settings.SPHINX_CONFIG_PATH]
    if rotate:
        calls.append('--rotate')

    call(calls)


def start_sphinx():
    """
    Starts sphinx.  Note this is only to be used in dev and test environments.
    """

    call([settings.SPHINX_SEARCHD, '--config',
        settings.SPHINX_CONFIG_PATH])


def stop_sphinx():
    """
    Stops sphinx.  Note this is only to be used in dev and test environments.
    """

    call([settings.SPHINX_SEARCHD, '--stop', '--config',
        settings.SPHINX_CONFIG_PATH])

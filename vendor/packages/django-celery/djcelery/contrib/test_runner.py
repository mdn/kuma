from __future__ import absolute_import

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

USAGE = """\
Custom test runner to allow testing of celery delayed tasks.
"""


class CeleryTestSuiteRunner(DjangoTestSuiteRunner):
    """Django test runner allowing testing of celery delayed tasks.

    All tasks are run locally, not in a worker.

    To use this runner set ``settings.TEST_RUNNER``::

        TEST_RUNNER = "djcelery.contrib.test_runner.CeleryTestSuiteRunner"

    """
    def setup_test_environment(self, **kwargs):
        super(CeleryTestSuiteRunner, self).setup_test_environment(**kwargs)
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Issue #75

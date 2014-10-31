============================
 Frequently Asked Questions
============================

Generating a template in a task doesn't seem to respect my i18n settings?
-------------------------------------------------------------------------

**Answer**: To enable the Django translation machinery you need to activate
it with a language. **Note**: Be sure to reset to the previous language when
done.

    >>> from django.utils import translation

    >>> prev_language = translation.get_language()
    >>> translation.activate(language)
    >>> try:
    ...     render_template()
    ... finally:
            translation.activate(prev_language)

The common pattern here would be for the task to take a ``language``
argument:

.. code-block:: python

    from celery.decorators import task

    from django.utils import translation
    from django.template.loader import render_to_string

    @task()
    def generate_report(template="report.html", language=None):
        prev_language = translation.get_language()
        language and translation.activate(language)
        try:
            report = render_to_string(template)
        finally:
            translation.activate(prev_language)
        save_report_somewhere(report)

The celery test-suite is failing
--------------------------------

**Answer**: If you're running tests from your Django project, and the celery
test suite is failing in that context, then follow the steps below. If the
celery tests are failing in another context, please report an issue to our
issue tracker at GitHub:

    http://github.com/ask/celery/issues/

That Django is running tests for all applications in ``INSTALLED_APPS``
by default is a pet peeve for many. You should use a test runner that either

    1) Explicitly lists the apps you want to run tests for, or

    2) Make a test runner that skips tests for apps you don't want to run.

For example the test runner that celery is using:

    http://github.com/ask/celery/blob/f90491fe0194aa472b5aecdefe5cc83289e65e69/celery/tests/runners.py

To use this test runner, add the following to your ``settings.py``:

.. code-block:: python

    TEST_RUNNER = "djcelery.tests.runners.CeleryTestSuiteRunner",
    TEST_APPS = (
        "app1",
        "app2",
        "app3",
        "app4",
    )

Or, if you just want to skip the celery tests:

.. code-block:: python

    INSTALLED_APPS = (.....)
    TEST_RUNNER = "djcelery.tests.runners.CeleryTestSuiteRunner",
    TEST_APPS = filter(lambda k: k != "celery", INSTALLED_APPS)


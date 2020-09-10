===============
Feature toggles
===============

MDN uses `feature toggles`_ to integrate un-finished feature changes as early
as possible, and to control the behavior of finished features.

Some site features are controlled using `django-waffle`_. You control these
features in the django admin site's `waffle section`_.

Some site features are controlled using `constance`_. You control these
features in the django admin site's `constance section`_.

Waffle features
===============

Switches
--------

`Waffle switches`_ are simple booleans - they are either on or off.

* ``application_ACAO`` - Enable Access-Control-Allow-Origin=0 header.
* ``foundation_callout`` - Show foundation donate homepage tile
* ``helpful-survey-2`` - Enable 2017 Helpfulness Survey
* ``registration_disabled`` - Enable/disable new user registration.
* ``store_revision_ips`` - Save request data, including the IP address, to
  enable marking revisions as spam.
* ``welcome_email`` - Send welcome email to new user registrations.
* ``wiki_spam_training`` - Call Akismet to check submissions, but don't block
  due to detected spam or Akismet errors.
* ``developer_needs`` - Enable/disable the developer needs survey banner


Flags
-----

`Waffle flags`_ control behavior by specific users, groups, percentages, and
other advanced criteria.

* ``contrib_beta`` - Enable/disable the contributions popup and pages
* ``kumaediting`` - Enable/disable wiki editing.
* ``developer_needs`` - Enable/disable the MDN developer needs survey banner
* ``page_move`` - (deprecated) enable/disable page move feature.
* ``section_edit`` - Show section edit buttons.
* ``sg_task_completion`` - Enable the Survey Gizmo pop-up.
* ``spam_admin_override`` - Tell Akismet that edits are never spam.
* ``spam_checks_enabled`` - Toggle spam checks site wide.
* ``spam_spammer_override`` - Tell Akismet that edits are always spam.
* ``spam_submissions_enabled`` - Toggle Akismet spam/spam submission ability.
* ``spam_testing_mode`` - Tell Akismet that edits are tests, not real content.
* ``subscription_banner`` - Enable/disable the subscriptions banner
* ``subscription_form`` - Enable/disable the subscriptions form

Constance features
==================

Constance configs let us set operational *values* for certain features in the
database - so we can control them without changing code. They are all listed
and documented in the admin site's `constance section`_.

.. _feature toggles: https://en.wikipedia.org/wiki/Feature_toggle
.. _django-waffle: https://waffle.readthedocs.io/en/latest/
.. _waffle section: http://localhost:8000/admin/waffle/
.. _constance: https://github.com/comoga/django-constance
.. _constance section: http://localhost:8000/admin/constance/config/
.. _Waffle switches: https://waffle.readthedocs.io/en/latest/types/switch.html
.. _Waffle flags: https://waffle.readthedocs.io/en/latest/types/flag.html
.. _PR 3331: https://github.com/mdn/kuma/pull/3331

Using Traffic Cop for A/B Testing
==================================

Traffic Cop is a lightweight JavaScript library that allows conducting content experiments on MDN without the need for third party tools such as Optimizely. Traffic Cop also respects user privacy, and will not run if `Do Not Track <https://en.wikipedia.org/wiki/Do_Not_Track>`_ is enabled.

On MDN, Traffic Cop will also not run for logged in users. Here's how to implement a Traffic Cop content experiment.

The first task is to choose your control page and create your tests pages Here we will use the scenario of testing a new feature on MDN. The new feature involved replacing the static examples on top, with an interactive editor.

First we choose our control page. For this example, we will use:

`https://developer.mozilla.org/docs/Experiment:ExperimentName/Array.prototype.push() <https://developer.mozilla.org/docs/Experiment:ExperimentName/Array.prototype.push()>`_

Next we need our test page. The convention on MDN is to first create a base page that follows a naming convention such as:

`https://developer.mozilla.org/docs/Experiment:ExperimentName/
<https://developer.mozilla.org/docs/Experiment:ExperimentName/>`_

With the base page created, we next create out test variation of our chosen page. To do this, navigate to:

`https://developer.mozilla.org/docs/Experiment:ExperimentName/Array.prototype.push()
<https://developer.mozilla.org/docs/Experiment:ExperimentName/Array.prototype.push()>`_

You should should now be presented with an editing interface to create the new page.

Switch back to the control page, and click the ``Edit`` button. Switch the editor to source mode and copy all of the contents inside the editor. Switch back to our test, ensure the editor is set to source mode, and paste the content you just copied.

You can now go ahead and make the changes you wish to user test. Once you are complete, go ahead and publish the page.

The JavaScript
--------------

Let us first add the JavaScript code to initialise and configure Traffic Cop.

Inside ``kuma\static\js``, create a new file called some like ``experiment-experiment-name.js`` and paste the following code into the file:

.. code-block:: javascript
    :linenos:

    (function() {
        'use strict';

        var cop = new Mozilla.TrafficCop({
            id: 'experiment-experiment-name',
            variations: {
                'v=a': 50, // control
                'v=b': 50 // test
            }
        });

        cop.init();
    })(window.Mozilla);

This will initialise Traffic Cop, set up an experiment with the id ``experiment-experiment-name``, and lastly define a 50/50 split between the control, and the test page.

Define your bundle
------------------

Next we need to add an entry into ``kuma\settings\common.py`` to identify the test, and the related JS that will be injected. Find the following line in ``common.py``::

        PIPELINE_JS = {

Just before the closing ``}`` add a block such as the following:

.. code-block:: python
    :linenos:

        'experiment-experiment-name': {
            'source_filenames': (
                'js/libs/mozilla.dnthelper.js',
                'js/libs/mozilla.cookiehelper.js',
                'js/libs/mozilla.trafficcop.js',
                'js/experiment-experiment-name.js',
            ),
            'output_filename': 'build/js/experiment-experiment-name.js',
        },

NOTE: The key here ``experiment-experiment-name`` needs to match the ``id`` you specified in your JS file above.

Identify your A/B test pages
----------------------------

The final step is to identify the pages to the back-end so it will know where to direct traffic based on the URL parameter that will be added by Traffic Cop. Inside ``kuma\settings\content_experiments.json`` add the following:

.. code-block:: json
    :linenos:

        [
            {
                "id": "experiment-experiment-name",
                "ga_name": "experiment-name",
                "param": "v",
                "pages": {
                    "en-US:Web/JavaScript/Reference/Global_Objects/Array/push": {
                        "a": "Web/JavaScript/Reference/Global_Objects/Array/push",
                        "b": "Experiment:ExperimentName/Array.prototype.push()"
                    },
                }
            }
        ]

There are a couple of important points to note here:

1. We are leaving of the domain, as well as the ``docs/`` part of the url.
2. As with the entry in ``common.py``, the ``id`` here matches the ``id`` in your JS file, tying it all together.
3. The ``param`` value, needs to match the string you specified inside the ``variations`` block in your JS
4. The first part of our key under ``pages`` above, identifies the locale to which this will apply, ``en-US`` in this case.
5. The key for the two pages listed next, needs to match the values you used as the parameter value inside ``variations`` in your JS file earlier.

Testing your experiment
-----------------------

With you local instance of Kuma running, navigate to the page you defined as your control. In this example:

`http://localhost:8000/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/push
<http://localhost:8000/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/push>`_

NOTE: You should not be logged in to MDN, and ensure that Do Not Track is disabled.

Your experiment JavaScript code bundle defined in ``common.py`` should be injected into the page, and Traffic Cop will add a URL parameter to the page that is either ``v=a`` or ``v=b``. Depending on which, you will either see the control(a), or the variation(b).

You can also force a specific page to load by appending ``?v=a`` or, ``?v=a`` manually to the control page URL.

If all the above works as expected, open up a pull request, and tag someone on MDN for reivew.

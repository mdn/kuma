.. This Source Code Form is subject to the terms of the Mozilla Public
.. License, v. 2.0. If a copy of the MPL was not distributed with this
.. file, You can obtain one at http://mozilla.org/MPL/2.0/.

========================================
Coding Conventions and Other Coding Info
========================================

This document contains useful information about our coding conventions, and
things to watch out for, etc.


Tests
=====

* Avoid naming test files ``test_utils.py``, since we use a library with the
  same name. Use ``test__utils.py`` instead.

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the ``TestCase``
  class.

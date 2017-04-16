==================
Werkzeug Changelog
==================

.. module:: werkzeug

This file lists all major changes in Werkzeug over the versions.
For API breaking changes have a look at :ref:`api-changes`, they
are listed there in detail.

.. include:: ../CHANGES

.. _api-changes:

API Changes
===========

`0.5`
    -   Werkzeug switched away from wsgiref as library for the builtin
        webserver.
    -   The `encoding` parameter for :class:`Template`\s is now called
        `charset`.  The older one will work for another two versions
        but warn with a :exc:`DeprecationWarning`.
    -   The :class:`Client` has cookie support now which is enabled
        by default.
    -   :meth:`BaseResponse._get_file_stream` is now passed more parameters
        to make the function more useful.  In 0.6 the old way to invoke
        the method will no longer work.  To support both newer and older
        Werkzeug versions you can add all arguments to the signature and
        provide default values for each of them.
    -   :func:`url_decode` no longer supports both `&` and `;` as
        separator.  This has to be specified explicitly now.
    -   The request object is now enforced to be read-only for all
        attributes.  If your code relies on modifications of some values
        makes sure to create copies of them using the mutable counterparts!
    -   Some data structures that were only used on request objects are
        now immutable as well.  (:class:`Authorization` / :class:`Accept`
        and subclasses)
    -   `CacheControl` was splitted up into :class:`RequestCacheControl`
        and :class:`ResponseCacheControl`, the former being immutable.
        The old class will go away in 0.6
    -   undocumented `werkzeug.test.File` was replaced by
        :class:`FileWrapper`.
    -   it's not longer possible to pass dicts inside the `data` dict
        in :class:`Client`.  Use tuples instead.
    -   It's save to modify the return value of :meth:`MultiDict.getlist`
        and methods that return lists in the :class:`MultiDict` now.  The
        class creates copies instead of revealing the internal lists.
        However :class:`MultiDict.setlistdefault` still (and intentionally)
        returns the internal list for modifications.

`0.3`
    -   Werkzeug 0.3 will be the last release with Python 2.3 compatibility.
    -   The `environ_property` is now read-only by default.  This decision was
        made because the request in general should be considered read-only.

`0.2`
    -   The `BaseReporterStream` is now part of the contrib module, the
        new module is `werkzeug.contrib.reporterstream`.  Starting with
        `0.3`, the old import will not work any longer.
    -   `RequestRedirect` now uses a 301 status code.  Previously a 302
        status code was used incorrectly.  If you want to continue using
        this 302 code, use ``response = redirect(e.new_url, 302)``.
    -   `lazy_property` is now called `cached_property`.  The alias for
        the old name will disappear in Werkzeug 0.3.
    -   `match` can now raise `MethodNotAllowed` if configured for
        methods and there was no method for that request.
    -   The `response_body` attribute on the response object is now called
        `data`.  With Werkzeug 0.3 the old name will not work any longer.
    -   The file-like methods on the response object are deprecated.  If
        you want to use the response object as file like object use the
        `Response` class or a subclass of `BaseResponse` and mix the new
        `ResponseStreamMixin` class and use `response.stream`.

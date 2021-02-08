===================
Rendering Documents
===================

Kuma's wiki format is a restricted subset of HTML, augmented with KumaScript
macros ``{{likeThis}}`` that render to HTML for display. Rendering is done
in several steps, many of which are stored in the database for read-time
performance.

.. source is at
   https://docs.google.com/drawings/d/1dkdxQ-dDUZi_OpIdEOw9kYoIp43jqAyKBoxS1CmXPWs/edit?usp=sharing

.. image:: /images/rendering.*

A revision goes through several rendering steps before it appears on the site:

1. A user submits new content, and Kuma stores it as :ref:`revision-content`
2. Kuma bleaches and filters the content to create :ref:`bleached-content`
3. KumaScript renders macros and returns :ref:`kumascript-content`
4. Kuma bleaches and filters the content again to create :ref:`rendered-content`
5. Kuma divides and processes the content into :ref:`body-html`, :ref:`quick-links-html`, :ref:`toc-html`, :ref:`summary-text-and-html`

There are other rendered outputs:

* Kuma normalizes the :ref:`revision-content` into the :ref:`diff-format` to comparing revisions
* Kuma filters the :ref:`revision-content` and adds section IDs to create the :ref:`triaged-content` for updating pages
* KumaScript renders the :ref:`triaged-content` as :ref:`preview-content`
* Kuma filters the :ref:`bleached-content` and adds section IDs to publish the :ref:`raw-content`
* Kuma extracts code sections from the :ref:`rendered-content` to flesh out a :ref:`live-sample`
* Kuma extracts the text from the :ref:`rendered-content` for the :ref:`search-content`

.. _revision-content:

Revision content
================
:doc:`CKEditor </ckeditor>` provides a visual HTML editor for MDN writers.  The
raw HTML returned from CKEditor is stored in the Kuma database for further
processing.

source
   User-entered content, usually via CKEditor from the `edit view`_ (URLs ending with ``$edit``)

   Developer-submitted content via an HTTP ``PUT`` to the `API view`_ (URLs ending in ``$api``)
displayed on MDN
   "Revision Source" section of the `revision detail view`_ (URLs ending with
   ``$revision/<id>``), in a ``<pre>`` tag
database
   ``wiki_revision.content``
code
   ``kuma.wiki.models.Revision.content``

To illustrate rendering, consider a new document published at
`/en-US/docs/Sandbox/simple`_ with this *Revision content*:

.. code-block:: html

   <p>{{ CSSRef }}</p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color:red">I am red.</p>

   <h2>Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li>{{HTMLElement('div')}}</li>
    <li><a href="/en-US/docs/NewDocument">A new document</a></li>
   </ul>

   <div class="button" onclick="alert('hacked!');"></div>

   <script>
     alert('How about this?');
   </script>

This document has elements that highlight different areas of rendering:

* A sidebar macro CSSRef_, which will be rendered by KumaScript and extracted for display
* A ``<h2>`` tag, which will gain an ``id`` attribute
* A list of three links:
   1. An HTML link to an existing document
   2. A reference macro HTMLElement_ which will be rendered by KumaScript
   3. An HTML link to a new document, which will get ``rel="nofollow"`` and ``class="new"`` attributes
* An ``onclick`` attribute, added in Source mode, which will be removed
* A ``<script>`` section, added in Source mode, which will be escaped

CKEditor has partial support for restricting content to the HTML subset
allowed for display. It also enforces a style where paragraphs (``<p>``)
are split by empty lines, start at the first column, and are closed on
the same line. Nested elements are indented one space. Plain text is wrapped
in ``<p>`` tags by default. KumaScript macros, such as ``{{CSSRef}}``, are
treated as plain text by CKEditor, so they are also wrapped in ``<p>`` tags.

Writers can also switch to "Source" mode, which permits direct editing of the
HTML, avoiding formatting and content restrictions. This can be used to attempt
to inject scripts like a ``onclick`` attribute or a ``<script>``. These
attempts are stored in the revision content.

The `PUT API`_ can also be used to add new revisions. This experimental API is
for staff only at this time.

.. _`edit view`: https://developer.mozilla.org/en-US/docs/Sandbox/simple$edit
.. _`API view`: https://developer.mozilla.org/en-US/docs/Sandbox/simple$api
.. _`revision detail view`: https://developer.mozilla.org/en-US/docs/Sandbox/simple$revision/1454597
.. _`/en-US/docs/Sandbox/simple`: https://developer.mozilla.org/en-US/docs/Sandbox/simple
.. _CSSRef: https://github.com/mdn/kumascript/blob/master/macros/CSSRef.ejs
.. _HTMLElement: https://github.com/mdn/kumascript/blob/master/macros/HTMLElement.ejs
.. _`PUT API`: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Tools/PUT_API

.. _bleached-content:

Bleached content
================
A revision can contain invalid markup, or elements that are not allowed on
MDN. When a new revision is created, the related document is updated in
``revision.make_current()``. This includes updating the title, path, and
tags, and also cleaning the content and saving it on the Document record.

source
   :ref:`revision-content`, processed with multiple filters
displayed on MDN
   The `API view`_ (URLs ending in ``$api``)
database
   ``wiki_document.html`` for current revision, not stored for historical revisions
code
   ``kuma.wiki.models.Document.get_html()`` (current revision, cached)

   ``kuma.wiki.models.Revision.content_cleaned`` (any revision, dynamically generated)

The *Bleached content* of the simple document looks like this:

.. code-block:: html

   <p>{{ CSSRef }}</p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color: red;">I am red.</p>

   <h2>Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li>{{HTMLElement('div')}}</li>
    <li><a href="/en-US/docs/NewDocument">A new document</a></li>
   </ul>

   <div class="button"></div>

   &lt;script&gt;
     alert('How about this?');
   &lt;/script&gt;

The first step of cleaning is "bleaching". The bleach_ library parses the
raw HTML and drops any tags, attributes, or styles that are not on the
`allowed lists`_. In the simple document, this step drops the ``onclick``
attribute from the ``<div>``, and escapes the ``<script>`` section.

Next, the HTML is tokenized by html5lib_. The content is parsed for ``<iframe>``
elements, and any ``src`` attributes that refer to disallowed domains are
dropped.

The tokenized document is serialized back to HTML, which may make
changes to whitespace or attribute order. In the simple document, this step
adds the extra space in ``style="color: red"``.

.. _bleach: https://github.com/mozilla/bleach
.. _`allowed lists`: https://github.com/mdn/kuma/blob/master/kuma/wiki/constants.py
.. _html5lib: https://github.com/html5lib/html5lib-python

.. _kumascript-content:

KumaScript content
==================
KumaScript macros are represented by text content in two curly braces, and
``{{lookLike('this')}}``. The KumaScript service processes these macros and
replaces them with plain HTML. This intermediate representation is not stored,
but instead is further processed to generate the :ref:`rendered-content`.

source
   :ref:`bleached-content`, processed by KumaScript
displayed on MDN
   *not published*
database
   Errors at ``wiki_document.rendered_errors``, content not stored
code
   Errors at ``kuma.wiki.models.Document.rendered_errors``, content not stored

The *KumaScript content* for the simple document looks like this:

.. code-block:: html

   <p><section class="Quick_links" id="Quick_Links"><ol><li><strong><a href="/en-US/docs/Web/CSS">CSS</a></strong></li><li><strong><a href="/en-US/docs/Web/CSS/Reference">CSS Reference</a></strong></li></ol></section></p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color: red;">I am red.</p>

   <h2>Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li><a href="/en-US/docs/Web/HTML/Element/div" title="The HTML Content Division element (&lt;div&gt;) is the generic container for flow content. It has no effect on the content or layout until styled using CSS."><code>&lt;div&gt;</code></a></li>
    <li><a href="/en-US/docs/NewDocument">A new document</a></li>
   </ul>

   <div class="button"></div>

   &lt;script&gt;
     alert('How about this?');
   &lt;/script&gt;

In the sample document, the ``{{CSSRef}}`` macro renders a sidebar.  It uses
data from the `mdn/data project`_ (fetched from GitHub), and the child pages of
the CSS topic index (fetched from `Web/CSS$children`_ on the Kuma API server).

Because the sample document isn't a real CSS reference page, the sidebar is
smaller than usual. The data may specify that a page is in one or
more groups, and a cross-reference should be added to the sidebar. For example,
on `Web/CSS/@media`_, the `mdn/data JSON`_ says it is in the "Media Queries"
group, and the cross-reference is populated from API data feteched from
`Web/CSS/Media_queries$children`_. These data-driven elements can cause the
sidebar to grow to several kilobytes.

The ``{{HTMLElement('div')}}`` macro also requires metadata from the ``<div>``
page, fetched from `Web/HTML/Element/div$json`_ on the Kuma API server, to
populate the ``title`` attribute of the link.

Macros are implemented as `Embedded JavaScript templates`_ (``.ejs`` files),
which mix JavaScript code with HTML output. The `macro dashboard`_ has a list
of macros, provided by the KumaScript service, as well as the count of pages
using the macros, populated from site search. The macro source is stored in
the KumaScript repo, such as CSSRef.ejs_ and HTMLElement.ejs_. Macro names are
case-insenstive, so ``{{CSSRef}}`` is the same as ``{{cssref}}``.

If KumaScript encounters an issue during rendering, the error
is encoded and returned in an HTTP header, in a format compatible with FireLogger_.
These errors are stored as JSON in ``wiki_document.rendered_errors``. The
rendered HTML isn't stored, but it passed for further processing. Moderators
frequently review `documents with errors`_, and fix those that they can fix.

.. _`mdn/data project`: https://github.com/mdn/data
.. _`Web/CSS$children`: https://developer.mozilla.org/en-US/docs/Web/CSS$children
.. _`Web/CSS/@media`: https://developer.mozilla.org/en-US/docs/Web/CSS/@media
.. _`mdn/data JSON`: https://github.com/mdn/data/blob/master/css/at-rules.json
.. _`Web/CSS/Media_queries$children`: https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries$children
.. _`Web/HTML/Element/div$json`: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div$json
.. _`div page metadata`: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div$json
.. _`Embedded JavaScript templates`: https://www.ejs.co/
.. _`macro dashboard`: https://developer.mozilla.org/en-US/dashboards/macros
.. _`CSSRef.ejs`: https://github.com/mdn/kumascript/blob/master/macros/CSSRef.ejs
.. _`HTMLElement.ejs`: https://github.com/mdn/kumascript/blob/master/macros/HTMLElement.ejs
.. _FireLogger: https://firelogger.binaryage.com
.. _`documents with errors`: https://developer.mozilla.org/en-US/docs/with-errors

Environment variables
---------------------
KumaScript macros often vary on page metadata, stored in the ``env`` object in
the render context. The render call is a ``POST`` where the body is the
:ref:`bleached-content`, and the headers include the encoded page metadata:

id
   The database ID of the document, like ``233925``
locale
   The locale of the page, like ``"en-US"``
modified
   The timestamp of the document modification time, like ``1548278930.0``
path
   The URL path of the page, like ``/en-US/docs/Sandbox/simple``
review_tags
   A list of review tags, like ``["technical", "editorial"]``
revision_id
   The database ID of the revision, like ``1438410``
slug
   The slug section of the URL, like ``Sandbox/simple``
tags
   A list of document tags for the page, like ``[]`` or ``["CSS"]``
title
   The document title, like ``"A simple page"``
url
   The full URL of the page, forced to ``http``, like ``http://developer.mozilla.org/en-US/docs/Sandbox/simple``.

Macro rendering speed
---------------------
It is unpredictable how long it will take to render the macros on a page.
After editing, a render is requested, and if it returns quickly, then the
rendered page is displayed. Otherwise, rendering is queued as a background
task, and the user sees a message that rendering is in progress.

Macros vary on rendering time, stability, and ease of testing based on where
they get their data. From simplest to most complex:

functional
   The output varies only on the macro inputs, like SimpleBadge_
environment data
   The output varies on the environment variables, like ObsoleteBadge_
local data
   The output varies on data packaged with KumaScript, like SpecName_
   (from SpecData.json_) or Compat_ (from the npm-installed
   `browser-compat-data project`_)
Kuma data
   The output varies on data gathered from `Kuma API calls`_ to an
   in-cluster dedicated Kuma API server, like Index_, which calls
   the ``$children`` API, or HTMLElement_, which calls the
   ``$json`` API.
external data
   The output varies on data from an external data source, like
   Bug_ (loads data from the Bugzilla_ API) or CSSRef_ (loads data from the
   `mdn/data project`_ via the GitHub API)

.. _SimpleBadge: https://github.com/mdn/kumascript/blob/master/macros/SimpleBadge.ejs
.. _obsolete_inline: https://github.com/mdn/kumascript/blob/master/macros/obsolete_inline.ejs
.. _ObsoleteBadge: https://github.com/mdn/kumascript/blob/master/macros/ObsoleteBadge.ejs
.. _`environment variables`: https://github.com/mdn/kuma/blob/77477d345c2513b9619920fd46174e0120b273c8/kuma/wiki/kumascript.py#L104-L115
.. _`SpecName`: https://github.com/mdn/kumascript/blob/master/macros/SpecName.ejs
.. _`SpecData.json`: https://github.com/mdn/kumascript/blob/master/macros/SpecData.json
.. _`browser-compat-data project`: https://github.com/mdn/browser-compat-data
.. _`NPM module`: https://www.npmjs.com/package/mdn-browser-compat-data
.. _Index: https://github.com/mdn/kumascript/blob/master/macros/Index.ejs
.. _Bug: https://github.com/mdn/kumascript/blob/master/macros/bug.ejs
.. _Bugzilla: https://bugzilla.mozilla.org
.. _Compat: https://github.com/mdn/kumascript/blob/master/macros/Compat.ejs
.. _`Kuma API Calls`: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Tools/Document_parameters#Document_metadata_resources

.. _rendered-content:

Rendered content
================
*Rendered content* is :ref:`kumascript-content` that has been cleaned up
using the same process as :ref:`bleached-content`.  This ensures that escaping
issues in KumaScript macros do not affect the security of users on displayed
pages.

source
   Bleached :ref:`kumascript-content`
displayed on MDN
   *not published*
database
   ``wiki_document.rendered_html``
code
   ``kuma.wiki.models.Document.get_rendered()``

The *Rendered content* for the simple document looks like this:

.. code-block:: html

   <p></p><section class="Quick_links" id="Quick_Links"><ol><li><strong><a href="/en-US/docs/Web/CSS">CSS</a></strong></li><li><strong><a href="/en-US/docs/Web/CSS/Reference">CSS Reference</a></strong></li></ol></section><p></p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color: red;">I am red.</p>

   <h2>Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li><a href="/en-US/docs/Web/HTML/Element/div" title="The HTML Content Division element (&lt;div>) is the generic container for flow content. It has no effect on the content or layout until styled using CSS."><code>&lt;div&gt;</code></a></li>
    <li><a href="/en-US/docs/NewDocument">A new document</a></li>
   </ul>

   <div class="button"></div>

   &lt;script&gt;
     alert('How about this?');
   &lt;/script&gt;

The parser doesn't allow ``<section>`` as a child element of ``<p>``, so the
serializer closes the tag with a ``</p>``, and adds another empty paragraph
element after the section. This is a side-effect of the differences between the
editing format, where ``{{CSSRef}}`` is text that needs to be in a paragraph
element, and the rendered content, where the macro is expanded as a
``<section>``.

.. _body-html:

Body HTML
=========
The "middle" of a wiki document is populated by the *Body HTML*.

source
   Extracted from :ref:`rendered-content`, cached in the database
displayed on MDN
   On the `displayed page`_, in an ``<article>`` element
database
   ``wiki_document.body_html``
code
   ``kuma.wiki.models.Document.get_body_html()``

The *Body HTML* for the simple document looks like this:

.. code-block:: html

   <p></p><p></p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color: red;">I am red.</p>

   <h2 id="Some_Links">Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li><a href="/en-US/docs/Web/HTML/Element/div" title="The HTML Content Division element (&lt;div>) is the generic container for flow content. It has no effect on the content or layout until styled using CSS."><code>&lt;div&gt;</code></a></li>
    <li><a rel="nofollow" href="/en-US/docs/NewDocument" class="new">A new document</a></li>
   </ul>

   <div class="button"></div>

   &lt;script&gt;
     alert('How about this?');
   &lt;/script&gt;

The section ``<section id="Quick_links">`` is discarded, leaving the empty
``<p></p>`` elements from the :ref:`rendered-content`. This can cause annoying
empty space at the top of a document.

IDs are injected into header elements (such as ``id="Some_Links"``),
based on the header text.

Any links on the page are checked to see if they are links to other wiki
pages, and if the destination page exists. The link to ``a_new_document``
gains a ``rel="nofollow"`` as well as ``class="new"``, to tell crawlers
and humans that the link is to a page that hasn't been written yet.

.. _`displayed page`: https://developer.mozilla.org/en-US/docs/Sandbox/simple

.. _quick-links-html:

Quick links HTML
================
The sidebar, on pages that include it, is populated from the *quick links html*.

source
   Extracted from :ref:`rendered-content`, cached in the database
displayed on MDN
   On the `displayed page`_, in a ``<div class="quick-links" id="quick-links">`` element
database
   ``wiki_document.quick_links_html``
code
   ``kuma.wiki.models.Document.get_quick_links_html()``

For the simple document, the *Quick links HTML* looks like this:

.. code-block:: html

   <ol><li><strong><a href="/en-US/docs/Web/CSS">CSS</a></strong></li><li><strong><a href="/en-US/docs/Web/CSS/Reference">CSS Reference</a></strong></li></ol>

The content of ``<section id="Quick_Links">`` is extracted from the rendered
HTML. It is processed to annotate any new links with ``rel="nofollow"`` and
``class="new"``.

.. _toc-html:

ToC HTML
========
The table of contents is populated from the ``<h2>`` elements of the
:ref:`rendered-content`, if any, and appears as a floating "Jump to" bar when
included. The "Jump to" bar can be supressed in editing mode by opening "Edit
Page Title and Properties", and setting TOC to "No table of contents".
The JavaScript can also decide to keep the bar hidden, such as when there
is a single heading. Even when not shown, the *ToC HTML* is generated and cached.

source
   Extracted from :ref:`rendered-content`, cached in the database
displayed on MDN
   On the `displayed page`_, in an ``<ol class="toc-links">`` element
database
   ``wiki_document.toc_html``
code
   ``kuma.wiki.models.Document.get_toc_html()``

For the simple document, the *ToC HTML* looks like this:

.. code-block:: html

   <li><a rel="internal" href="#Some_Links">Some Links</a>

.. _summary-text-and-html:

Summary text and HTML
=====================
Summary text is used for SEO purposes. An editor can specify the summary text
by adding an ``id="Summary"`` attribute to the element that contains the
summary. Otherwise, the code extracts a summary from the first non-empty
paragraph.

source
   Extracted from :ref:`rendered-content`, cached in the database
displayed on MDN (text)
   On the `displayed page`_, in the ``<meta name"description">`` element and other elements

   In `internal search results`_, as the search hit summary

   On some document lists, like `Documents by tag`_

displayed on MDN (HTML)
   The `page metadata view`_ (URLs ending in ``$json``)

   The `summary view`_ (URLs with ``?summary=1``) (currently broken, see `bug 1523955`_)

   KumaScript macros that use page metadata, for example to populate ``title`` attributes
database
   ``wiki_document.summary_text``

   ``wiki_document.summary_html``
code
   ``kuma.wiki.models.Document.get_summary_text()``

   ``kuma.wiki.models.Document.get_summary_html()``


For the simple document, the summary text is:

.. code-block:: html

   I am a simple document with a CSS sidebar.

The summary HTML is:

.. code-block:: html

   I am a <strong>simple document</strong> with a CSS sidebar.

.. _`internal search results`: https://developer.mozilla.org/en-US/search?q=%22I+am+a+simple+document%22&none=none
.. _`Documents by tag`: https://developer.mozilla.org/en-US/docs/tag/CSS
.. _`page metadata view`: https://developer.mozilla.org/en-US/docs/Sandbox/simple$json
.. _`summary view`: https://developer.mozilla.org/en-US/docs/Sandbox/simple?summary=1
.. _`bug 1523955`: https://bugzilla.mozilla.org/show_bug.cgi?id=1523955

.. _diff-format:

Diff format
===========
MDN moderators and localization leaders are interested in the changes to wiki
pages. They want to revert spam and vandalism, enforce documentation standards,
and learn about the writer community. They are focused on what changed between
document revisions. The differences format, or *Diff format*, is used to
highlight content changes.

source
   :ref:`revision-content`, pretty-printed with tidylib_, and
   compared to other revisions.
displayed on MDN
   `Revision comparison views`_ (URLs ending in ``$compare``)

   The `Revision dashboard`_

   `Page watch emails`_

   First edit emails, sent to content moderators

   `RSS and Atom feeds`_
database
   ``wiki_revision.tidied_content``
code
   ``kuma.wiki.models.Revision.get_tidied_content()``

The simple document in *Diff format* looks like this:

.. code-block:: html

   <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">
   <html>
     <head>
       <title></title>
     </head>
     <body>
       <p>
         {{ CSSRef }}
       </p>
       <p>
         I am a <strong>simple document</strong> with a CSS sidebar.
       </p>
       <p style="color:red">
         I am red.
       </p>
       <h2>
         Some Links
       </h2>
       <ul>
         <li>
           <a href="/en-US/docs/Web/HTML">The HTML Reference</a>
         </li>
         <li>{{HTMLElement('div')}}
         </li>
         <li>
           <a href="/en-US/docs/NewDocument">A new document</a>
         </li>
       </ul>
       <div class="button" onclick="alert('hacked!');"></div>
       <script>
       alert('How about this?');
       </script>
     </body>
   </html>

The :ref:`revision-content` is normalized using pytidylib_, a Python interface
to the C tidylib_ library, which turns the content into a well-structured HTML
4.01 document.

Content difference reports, or "diffs", are generated by a line-by-line
comparison of the content in *Diff format* of two revisions. Lines that differ
are dropped, so that the reports focus on just the changed content, often
without the wrapping HTML tags like ``<p></p>``. These diffs often contain line
numbers from the *Diff format*, which do not correspond to the line numbers in
the :ref:`revision-content` because of differences in formatting and
whitespace.

Because the *Diff format* can contain unsafe content, it is not displayed
directly on MDN. On `Revision comparison views`_, the `Revision dashboard`_,
and in feeds, two *Diff formats* are processed by `difflib.HtmlDiff`_ to
generate an HTML ``<table>`` showing only the changed lines, and with HTML
escaping for the content.

For emails, `difflib.unified_diff`_ generates a text-based difference
report, and it is sent as a plain-text email without escaping.

.. _pytidylib: https://pypi.org/project/pytidylib/
.. _tidylib: http://www.html-tidy.org/developer/
.. _`Revision comparison views`: https://developer.mozilla.org/en-US/docs/Sandbox/simple$compare?locale=en-US&to=1454597&from=1454596
.. _`Revision dashboard`: https://developer.mozilla.org/en-US/dashboards/revisions
.. _`Page watch emails`: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Tools/Page_watching
.. _`RSS and Atom feeds`: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Tools/Feeds
.. _`difflib.HtmlDiff`: https://docs.python.org/2/library/difflib.html#difflib.HtmlDiff
.. _`difflib.unified_diff`: https://docs.python.org/2/library/difflib.html#difflib.HtmlDiff

.. _triaged-content:

Triaged content
===============
When a document is re-edited, the :ref:`revision-content` of the current
revision is processed before being sent to the editor. This is a lighter
version of the full bleaching process used to create :ref:`bleached-content`
and :ref:`rendered-content`.

source
   :ref:`revision-content`, with further processing in ``RevisionForm``.
displayed on MDN
   Editing ``<textarea>`` in the `edit view`_ (URLs ending with ``$edit``)

   Editing ``<textarea`` in the `translate view`_ (URLs ending with ``$translate``)
database
   *not stored*
code
   *not available*

For the simple document, this is the *Triaged content*:

.. code-block:: html

   <p>{{ CSSRef }}</p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color:red">I am red.</p>

   <h2 id="Some_Links">Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li>{{HTMLElement('div')}}</li>
    <li><a href="/en-US/docs/NewDocument">A new document</a></li>
   </ul>

   <div class="button"></div>

   <script>
     alert('How about this?');
   </script>

The headers get IDs, based on the content, if they did not have them before.
For example, ``id="Some_Links"`` is added to the ``<h2>``.

A simple filter is applied that strips any attributes that start with
``on``, such as the scripting attempt ``onclick``. Further bleaching,
for example to remove the ``<script>``, is not applied.

CKEditor will perform additional parsing and formatting at load time. It will
sometimes notice the empty ``<div>`` and replace it with
``<div class="button">&nbsp;</div>``, especially if it is the last element
on the page. It may also remove the ``<script>`` element entirely.

If a writer makes a change, these backend and CKEditor changes will be
reflected in the new :ref:`revision-content`. This can confuse writers
("I didn't add those IDs!").

.. _`translate view`: https://developer.mozilla.org/en-US/docs/Sandbox/simple$translate?tolocale=fr

.. _preview-content:

Preview content
===============
When editing, a user can request a preview of the document. This sends the
in-progress document to editing, with a smaller list of environment variables.

source
   :ref:`triaged-content`, with CKEditor parsing, passed through KumaScript
output
   HTML content at ``/<locale>/docs/preview-wiki-content``
database
   *not stored*
code
   *not available*

The *Preview content* for the simple document is:

.. code-block:: html

   <p></p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color: red;">I am red.</p>

   <h2>Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li><a href="/en-US/docs/Web/HTML/Element/div" title="The HTML Content Division element (&lt;div>) is the generic container for flow content. It has no effect on the content or layout until styled using CSS."><code>&lt;div&gt;</code></a></li>
    <li><a href="/en-US/docs/NewDocument">A new document</a></li>
   </ul>

   <div class="button"></div>

   &lt;script&gt;
     alert('How about this?');
   &lt;/script&gt;

Fewer environment variables are passed to the KumaScript server for preview
than when generating the :ref:`kumascript-content`:

url
   The base URL of the website, like ``https://developer.mozilla.org/``
locale
   The locale of the request, like ``"en-US"``

Some macros use the absence of an environment variable to detect preview mode,
and change their output. For example, ``{{CSSRef}}`` notices that ``env.slug``
is not defined, and outputs an empty string, leaving ``<p></p>`` in the
preview output.

Other macros don't have specific code to detect preview mode, and have
KumaScript rendering errors in preview.

Some macros, like ``{{HTMLElement}}``, work as expected in preview.

.. _raw-content:

Raw content
===========
A ``?raw`` parameter can be added to the end of a document to request the
source for a revision. This is processed in a similar way to the
:ref:`triaged-content`, but from the :ref:`bleached-content`.

source
   :ref:`bleached-content`, with filters
output
   The page with a ``?raw`` query parameter
database
   *not stored*
code
   *not available*

For the simple document, this is the *raw content*:

.. code-block:: html

   <p>{{ CSSRef }}</p>

   <p>I am a <strong>simple document</strong> with a CSS sidebar.</p>

   <p style="color: red;">I am red.</p>

   <h2 id="Some_Links">Some Links</h2>

   <ul>
    <li><a href="/en-US/docs/Web/HTML">The HTML Reference</a></li>
    <li>{{HTMLElement('div')}}</li>
    <li><a href="/en-US/docs/NewDocument">A new document</a></li>
   </ul>

   <div class="button"></div>

   &lt;script&gt;
     alert('How about this?');
   &lt;/script&gt;

The :ref:`bleached-content` is parsed for filtering . The headers get IDs, based
on the content, if they did not have them before.  For example,
``id="Some_Links"`` is added to the ``<h2>``.

A simple filter is applied that strips any attributes that start with
``on``, such as the scripting attempt ``onclick``. However, this step should
do nothing, since these attribute are dropped when creating the
:ref:`bleached-content`.

.. _live-sample:

Live sample
============
`Live samples`_ are stored in document content. The content is then processed
to extract the CSS, JS, and HTML, and reformat them as a stand-alone HTML
document suitable for displaying in an ``<iframe>``.

source
   A section extracted from :ref:`rendered-content`, with further processing
output
   Live sample documents on a separate domain, such as https://mdn.mozillademos.org
database
   Not stored in the database, but cached
code
   ``kuma.wiki.Document.extract.code_sample(section_id)``

The simple document does not include one of these samples.
The `Live samples`_ page on MDN describes how the system works for content
authors, and includes a `live sample demo`_.

Most live samples are loaded in an ``<iframe>``, inserted by the macro
EmbedLiveSample_. If the sample doesn't work as an ``<iframe>``,
LiveSampleLink_ can be used instead. The ``<iframe src=`` URL is Kuma, running
on a different domain, such as https://mdn.mozillademos.org, and configured
to serve live samples (the `code sample view`_) and attachments. A separate
domain for user-created content, often served in an ``<iframe>``, mitigates
many security issues.

The live sample is cached on first access, and generated when requested.  The
extractor looks for ``<pre>`` sections with ``class="brush: html"``,
``"brush: css"``, and ``"brush: js"``, to find the sample content, and then
selectively un-escapes some HTML and CSS. These sections are used to
populate a basic HTML file.

There are other sample types that are not derived from wiki content.
These are out-of-scope for this document, but the most significant are listed
here for the curious:

* **Legacy samples**, like `cssref/background-attachment.html`_, are no longer maintained
  and are planned for removal (see `bug 1076893`_ and related bugs).
* **GitHub Live Samples**, like the `CSS circle demo`_, are maintained in an
  MDN repo like `mdn/css-examples`_, served by GitHub pages,
  and inserted with EmbedGHLiveSample_.
* **Interactive examples** are sourced in the
  `mdn/interactive-examples repository`_, deployed as a static website,
  inserted with the EmbedInteractiveExamples_ macro near the top of the page,
  and are displayed in an ``<iframe>``.

.. _`Live samples`: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Structures/Live_samples
.. _`live sample demo`: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Structures/Live_samples#Live_sample_demo
.. _`code sample view`: https://mdn.mozillademos.org/en-US/docs/MDN/Contribute/Structures/Live_samples$samples/Live_sample_demo?revision=1438808
.. _EmbedLiveSample: https://github.com/mdn/kumascript/blob/master/macros/EmbedLiveSample.ejs
.. _LiveSampleLink: https://github.com/mdn/kumascript/blob/master/macros/LiveSampleLink.ejs
.. _cssref/background-attachment.html: https://developer.mozilla.org/samples/cssref/background-attachment.html
.. _`bug 1076893`: https://bugzilla.mozilla.org/show_bug.cgi?id=1076893
.. _`CSS circle demo`: https://mdn.github.io/css-examples/shapes/overview/circle.html
.. _`mdn/css-examples`: https://github.com/mdn/css-examples
.. _EmbedGHLiveSample: https://github.com/mdn/kumascript/blob/master/macros/EmbedGHLiveSample.ejs
.. _`mdn/interactive-examples repository`: https://github.com/mdn/interactive-examples
.. _EmbedInteractiveExamples: https://github.com/mdn/kumascript/blob/master/macros/EmbedInteractiveExample.ejs


Future Changes
==============
Rendering evolved over years, and this document describes how it works, rather
than how it was designed. There are some potential changes that would simplify
rendering:

* Sidebar macros are heavy users of API data and require post-processing of the
  :ref:`rendered-content`. Sidebar generation could be moved into Kuma instead
  of being specified by a macro.
* The :ref:`diff-format` could be replaced by the :ref:`bleached-content`
  format, which would be stored for each revision rather than just for the most
  recent document.
* Content from editing could be normalized and filtered before storing as the
  :ref:`revision-content`. This may unify the :ref:`triaged-content`,
  :ref:`diff-format`, and :ref:`bleached-content`.
* The views that accept new revisions could add IDs to the content before
  storing the :ref:`revision-content`, rather than wait for the
  :ref:`triaged-content` or :ref:`body-html`.
* Developers could refactor the code to consistently access and generate
  content, rather than repeat filter logic in different forms and views.

History
=======
MDN has used different rendering processes in the past.

Prior to 2004, Netscape's DevEdge was a statically-generated website, with
content stored in a revision control system (CVS_ or similar). This was
shut down for a while, until Mozilla was able to negotiate a license for the
content.

From 2005 to 2008, MediaWiki_ was used as the engine of Mozilla Developer
Center. The DevEdge content was converted to `MediaWiki Markup`_.

From 2008 to 2011, `MindTouch DekiWiki`_ was used as the engine. MindTouch
migrated the MediaWiki content to the DekiWiki format, a restricted subset of
HTML, augmented with macros ("DekiScript"). During this period, the site was
rebranded as Mozilla Developer Network.

In 2011, Kuma was forked from Kitsune_, the Django-based platform for
support.mozilla.org_. The wiki format was as close as possible to the
DekiWiki format. A new service KumaScript_ was added to implement
DekiScript-style macros. The macros, also known as templates, were stored
as content in the database. The service had a ``GET`` API to render pages,
and a ``POST`` API to render previews.

In 2013, content zones were added, which allowed a "zone" of pages to have a
different style from the rest of the site. For example, the Firefox Zone of
all the documents under ``/Mozilla/Firefox`` had a logo and a shared
sub-navigation sidebar.  Sub-navigation was similar to quick links, identified
by ``<section id="Subnav">``, but stored on the "zone root"
(``/Mozilla/Firefox``) rather than generated by a macro.  Zones were part of an
effort to consolidate developer documentation on MDN.

In 2016, the macros were exported from the Kuma database into the
`macros folder in the KumaScript repository`_. The historical changes were
exported to `mdn/archived_kumascript`_. This made rendering faster, and
allowed code reviews and automated tests of macros, at the cost of requiring
review and a production push to deploy macro changes.

In 2018, the content zones feature was removed. This was part of an effort
to focus MDN Web Docs on common web platform technologies, and away from
Mozilla-specific documentation. The sub-navigation feature was dropped.

In 2019, the KumaScript engine and macros were modernized to use current
features of JavaScript, such as ``async`` / ``await``, rather than
libraries common in 2011. The API was also unified, so that both previews
and standard renders required a ``POST``.

.. _CVS: https://en.wikipedia.org/wiki/Concurrent_Versions_System
.. _MediaWiki: https://en.wikipedia.org/wiki/MediaWiki
.. _`MediaWiki Markup`: https://en.wikipedia.org/wiki/MediaWiki#Markup
.. _`MindTouch DekiWiki`: https://en.wikipedia.org/wiki/MindTouch
.. _Kitsune: https://github.com/mozilla/kitsune
.. _support.mozilla.org: https://support.mozilla.org/en-US/
.. _KumaScript: https://github.com/mdn/kumascript
.. _`macros folder in the KumaScript repository`: https://github.com/mdn/kumascript/commits/master/macros
.. _`mdn/archived_kumascript`: https://github.com/mdn/archived_kumascript

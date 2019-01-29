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

The main flow of rendering is:

* A document's new or updated content is stored as *revision content*
* The content is processed to create *cleaned content*, with macros and safe HTML
* The content is passed to KumaScript to create *KumaScript content*, with rendered macros
* The content is processed to create *rendered content*, and is only safe HTML
* This content is split up into *body HTML*, *quick links HTML*, *ToC HTML*, *summary HTML*, and *summary text*

There are secondary rendering flows as well:

* The *revision content* is normalized as the *diff format*, for comparing revisions
* The *revision content* is filtered into the *re-edit content* for editing
* The *re-edit content* is sent to KumaScript to create *preview content*
* The *cleaned content* is processed for *raw content*
* The *rendered content* is process to create a *live sample*

Revision content
================
:doc:`CKEditor </ckeditor>` is used to provide a visual HTML editor for MDN
writers.  The raw HTML returned from CKEditor is stored in the Kuma database
for further processing.

source
   User-entered content, usually via CKEditor and ``$edit`` view

   PUT ``$api``
on MDN
   "Revision Source" section of revision detail view (in ``<pre>`` tag)
database
   ``wiki_revision.content``
code
   ``Revision.content``

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

* A sidebar macro CSSRef_, which is rendered and extracted for display
* A ``<h2>`` tag, which gains an ``id`` attribute
* A list of three links: to an existing document, using a reference macro HTMLElement_, and to a new document
* An ``onclick`` attribute
* A ``<script>`` section

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

The PUT ``$API`` can also be used to add new revisions. This API is for staff
only at this time.

.. _`/en-US/docs/Sandbox/simple`: https://developer.mozilla.org/en-US/docs/Sandbox/simple
.. _CSSRef: https://github.com/mdn/kumascript/blob/master/macros/CSSRef.ejs
.. _HTMLElement: https://github.com/mdn/kumascript/blob/master/macros/HTMLElement.ejs

Cleaned content
===============
A revision can contain invalid markup, or elements that are not allowed on
MDN. When a new revision is created, the related document is updated in
``revision.make_current()``. This includes updating the title, path, and
tags, and also cleaning the content and saving it on the Document record.

source
   *revision content*, processed with multiple filters
on MDN
   ``$api`` endpoint
database
   ``wiki_document.html`` for current revision, not stored for historical revisions
code
   ``Document.get_html`` (current revision, cached), ``Revision.content_cleaned`` (any revision, dynamically generated)

The *cleaned content* of the simple document looks like this:

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
.. _`allowed lists`: https://github.com/mozilla/kuma/blob/master/kuma/wiki/constants.py
.. _html5lib: https://github.com/html5lib/html5lib-python

KumaScript content
==================
KumaScript macros are represented by text content in two curly braces, and
``{{lookLike('this')}}``. The KumaScript service processes these macros and
replaces them with plain HTML. This intermediate representation is not stored,
but instead is further processed to generate the rendered HTML.

source
   *cleaned content*, processed by KumaScript
on MDN
   *not published*
database
   Errors at ``wiki_document.rendered_errors``, content not stored
code
   Errors at ``Document.rendered_errors``, content not stored

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

In the sample document, the ``{{CSSRef}}`` macro renders a skeleton version of
the full sidebar. On pages like `Media queries`_, the sidebar grows to several
kilobytes, to bring in links to related CSS pages.  The
``{{HTMLElement('div')}}`` requires page data, which is gathered via a HTTP
request to a Kuma API server.

Macros are implemented as `Embedded JavaScript templates`_ (``.ejs`` files),
which mix JavaScript code with HTML output. The `macro dashboard`_ has a list
of macros, provided by the KumaScript service, as well as the count of pages
using the macros, populated from site search.

If KumaScript encounters an issue during rendering, the error
is encoded and returned in an HTTP header, in a format compatible with FireLogger_.
These errors are stored as JSON in ``wiki_document.rendered_errors``. The
rendered HTML isn't stored, but it passed for further processing. Moderators
frequently review `documents with errors`_, and fix those that they can fix.

Environment variables
---------------------
KumaScript macros often vary on page metadata, stored in the ``env`` object in
the render context. The render call is a ``POST`` where the body is the cleaned
format content, and the headers include the encoded page metadata:

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
   The output varies on data gathered from Kuma API calls to an
   in-cluster dedicated API server, like Index_, which calls
   the ``$children`` API, or HTMLElement_, which calls the
   ``$json`` API.
external data
   The output varies on data from an external data source, like
   Bug_ (loads data from the Bugzilla_ API) or CSSRef_ (loads data from the
   `mdn/data project`_ via the GitHub API)

.. _`Embedded JavaScript templates`: https://www.ejs.co/
.. _`macro dashboard`: https://developer.mozilla.org/en-US/dashboards/macros
.. _`Media queries`: https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries
.. _SimpleBadge: https://github.com/mdn/kumascript/blob/master/macros/SimpleBadge.ejs
.. _obsolete_inline: https://github.com/mdn/kumascript/blob/master/macros/obsolete_inline.ejs
.. _ObsoleteBadge: https://github.com/mdn/kumascript/blob/master/macros/ObsoleteBadge.ejs
.. _`environment variables`: https://github.com/mozilla/kuma/blob/77477d345c2513b9619920fd46174e0120b273c8/kuma/wiki/kumascript.py#L104-L115
.. _`SpecName`: https://github.com/mdn/kumascript/blob/master/macros/SpecName.ejs
.. _`SpecData.json`: https://github.com/mdn/kumascript/blob/master/macros/SpecData.json
.. _`browser-compat-data project`: https://github.com/mdn/browser-compat-data
.. _`NPM module`: https://www.npmjs.com/package/mdn-browser-compat-data
.. _Index: https://github.com/mdn/kumascript/blob/master/macros/Index.ejs
.. _Bug: https://github.com/mdn/kumascript/blob/master/macros/bug.ejs
.. _Bugzilla: https://bugzilla.mozilla.org
.. _`mdn/data project`: https://github.com/mdn/data
.. _FireLogger: https://firelogger.binaryage.com
.. _Compat: https://github.com/mdn/kumascript/blob/master/macros/Compat.ejs
.. _`documents with errors`: https://developer.mozilla.org/en-US/docs/with-errors

Rendered content
================
The content returned from KumaScript isn't stored, but is cleaned up using the
same process as *cleaned content*. This ensures that escaping issues in
KumaScript macros do not affect the security of users on displayed pages.

source
   *KumaScript content*, with further processing
on MDN
   *not published*
database
   ``wiki_document.rendered_html``
code
   ``Document.get_rendered()``

The *rendered content* for the simple document looks like this:

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

Body HTML
=========
The "middle" of a wiki document is populated by the *body HTML*.

source
   Extracted from *rendered content*
on MDN
   On wiki pages, in ``<article>`` element
database
   ``wiki_document.body_html``
code
   ``Document.get_body_html()``

The *body HTML* for the simple document looks like this:

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
``<p></p>`` elements from the *rendered content*. This can cause annoying
empty space at the top of a document.

IDs are injected into header elements (such as ``id="A_simple_document"``),
based on the header text.

Any links on the page are checked to see if they are links to other wiki
pages, and if the destination page exists. The link to ``a_new_document``
gains a ``rel="nofollow"`` as well as ``class="new"``, to tell crawlers
and humans that the link is to a page that hasn't been written yet.

Quick links HTML
================
The sidebar, on pages that include it, is populated from the *quick links html*.

source
   Extracted from *rendered content*
on MDN
   On wiki pages, in ``<div class="quick-links" id="quick-links">`` element
database
   ``wiki_document.quick_links_html``
code
   ``Document.get_quick_links_html()``

For the simple document, the *quick links HTML* looks like this:

.. code-block:: html

   <ol><li><strong><a href="/en-US/docs/Web/CSS">CSS</a></strong></li><li><strong><a href="/en-US/docs/Web/CSS/Reference">CSS Reference</a></strong></li></ol>

The content of ``<section id="Quick_Links">`` is extracted from the rendered
HTML. It is processed to annotate any new links with ``rel="nofollow"`` and
``class="new"``.

ToC HTML
========
The table of contents is populated from the ``<h2>`` elements, if any,
and appears as a floating "Jump to" bar when included.

source
   Extracted from *rendered content*
on MDN
   On wiki pages, in ``<ol class="toc-links">`` element
database
   ``wiki_document.toc_html``
code
   ``Document.get_toc_html()``

For the simple document, the *ToC HTML* looks like this:

.. code-block:: html

   <li><a rel="internal" href="#Some_Links">Some Links</a>

Summary text and HTML
=====================
Summary text is used for SEO purposes. An editor can specify the summary text
by adding a ``id="Summary"`` attribute. Otherwise, the code attempts to
extract a summary from the first paragraph.

source
   Extracted from *rendered content*
on MDN (text)
   On wiki pages, in ``<meta name"description">`` and other elements

   In internal search results

   On some document lists, like `Documents with no parent`_

on MDN (HTML)
   ``$json`` page metadata, other APIs

   KumaScript macros that use ``$json`` page data, for example to populate ``title`` attributes
database
   ``wiki_document.summary_text`` and ``wiki_document.summary_html``
code
   ``Document.get_summary_text()`` and ``Document.get_summary_html``


For the simple document, the summary text is:

.. code-block:: html

   I am a simple document with a CSS sidebar.

The summary HTML is:

.. code-block:: html

   I am a <strong>simple document</strong> with a CSS sidebar.

.. _`Documents with no parent`: https://developer.mozilla.org/en-US/docs/without-parent

Diff format
===========
MDN moderators and localization leaders are interested in the changes to wiki
pages. They want to revert spam and vandalism, enforce documentation standards,
and learn about the writer community. They are focused on what changed between
document revisions. The differences format, or *diff format*, is used to
highlight content changes.

source
   *revision content*, processed with Tidy
output
   `Revision comparison`_, `revision dashboard`_, page watch emails, first
   edit emails, RSS feeds, Atom feeds.
database
   ``wiki_revision.tidied_content``
code
   ``Revision.content_tidied``

The simple document in *diff format* looks like this:

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

The editing format is normalized using pytidylib_, a Python interface to the C
tidylib_ library, which turns the content into a well-structured HTML 4.01
document.

Content difference reports, or "diffs", are generated by comparing tidied
content to other tidied content, and removing lines that are the same between
revisions. These diffs often contain line numbers, which do not correspond to
the line numbers in the editing format, because of differences in formatting
whitespace.

.. _pytidylib: https://pypi.org/project/pytidylib/
.. _tidylib: http://www.html-tidy.org/developer/
.. _`Revision comparison`: https://developer.mozilla.org/en-US/docs/Web$compare?locale=en-US&to=1445176&from=1444948
.. _`revision dashboard`: https://developer.mozilla.org/en-US/dashboards/revisions

Re-edit content
===============
When a document is re-edited, the *revision content* of the current revision is
processed before being sent to the editor.

source
   *revision content*, with further processing in ``RevisionForm``.
output
   Editing input in the edit (``$edit``) and translation (``$translate``) views
database
   *not stored*
code
   *not available*

For the simple document, this is the content in *re-edit format*:

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
reflected in the new *revision content*. This can confuse writers
("I didn't add those IDs!").

Preview content
===============
When editing, a user can request a preview of the document. This sends the
in-progress document to editing, with a smaller list of environment variables.

source
   *revision content* or *re-edit content*, with CKEditor parsing, passed
   through KumaScript
output
   HTML content at ``/<locale>/docs/preview-wiki-content``
database
   *not stored*
code
   *not available*

The *preview content* for the simple document is:

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

The environment in preview is different than in regular KumaScript rendering:

url
   The base URL of the website, like ``https://developer.mozilla.org/``
locale
   The locale of the request, like ``"en-US"``

Some macros use the absence of an environment variable to detect preview mode,
and change their output. For example, ``{{CSSRef}}`` notices that ``env.slug``
is not defined, and outputs an empty string, leaving ``<p></p>`` in the
preview output.

Other macros don't have specific code to detect preview mode, and have
kumascript rendering errors.

Some macros, like ``{{HTMLElement}}``, can work as expected in preview.

Raw content
===========
A ``?raw`` parameter can be added to the end of a document to request the
source for a revision.

source
   *cleaned content*, with filters
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

The *cleaned content* is parsed for filtering . The headers get IDs, based on
the content, if they did not have them before.  For example,
``id="Some_Links"`` is added to the ``<h2>``.

A simple filter is applied that strips any attributes that start with
``on``, such as the scripting attempt ``onclick``. However, none of these
should remain in the *cleaned content*.

Live sample
============
`Live samples`_ are stored in document content. The content is then processed
to extract the CSS, JS, and HTML, and reformat them as a stand-alone HTML
document suitable for displaying in an ``<iframe>``.

source
   A section extracted from *rendered content*, with further processing
output
   Live sample documents on a separate domain, such as https://mdn.mozillademos.org
database
   Not stored in the database, but cached
code
   ``Document.extract_code_sample(section_id)``

`Live samples`_ are long, so the simple document does not include one.

.. _`Live samples`: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Structures/Live_samples

Future Changes
==============
Rendering evolved over years, and this document describes how it works, rather
than how it was designed. There are some potential changes that would simplify
rendering:

* Sidebar macros are heavy users of API data and require post-processing of the
  content. Sidebar generation could be moved into Kuma instead of being
  specified by a macro.
* The *diff format* could be replaced by the *cleaned content* format, which
  would be stored for each revision rather than just for the most recent
  document.
* Content from editing could be normalized and filtered before storing as the
  *revision content*. This may unify the *re-edit format*, *diff format*, and
  *cleaned content*
* Add IDs immediately to the *revision content*, rather than wait for the
  *re-edit format* or *body HTML*.
* Add more consistent ways to access and generate content, rather than
  repeating filter logic in different forms and views.

History
=======
MDN has used different rendering processes in the past.

Prior to 2004, Netscape's DevEdge was a statically-generated website, with
content stored in a revision control system (CSV_ or similar). This was
shut down for a while, until Mozilla was able to acquire the license for the
content.

From 2005 to 2008, MediaWiki_ was used as the engine of Mozilla Developer
Center. The DevEdge content was converted to `MediaWiki Markup`_.

From 2008 to 2011, `MindTouch DekiWiki`_ was used as the engine. MindTouch
performed the conversion of content from MediaWiki to DekiWiki format,
a restricted subset of HTML, augmented with macros ("DekiScript"). During this
period, the site was rebranded as Mozilla Developer Network.

In 2011, Kuma was forked from Kitsune_, the Django-based platform for
support.mozilla.org_. The wiki format was as close as possible to the
DekiWiki format. A new service KumaScript_ was added to implement
DekiScript-style macros. The macros, also known as templates, were stored
as content in the database. The service had a ``GET`` API to render pages,
and a ``POST`` API to render previews.

In 2013, content zones were added, which allowed a different style for
a zone of pages, such as a logo and sub-navigation for all the Firefox
documents under ``/Mozilla/Firefox``. Sub-navigation was similar to quick
links, identified by ``<section id="Subnav">``, but stored on the
"zone root" (``/Mozilla/Firefox``) rather than generated by a macro.
This was part of an effort to consolidate developer documentation on MDN.

In 2016, the macros were exported from the Kuma database into the
`macros folder in the KumaScript repository`_. The historical changes were
exported to `mdn/archived_kumascript`_. This made rendering faster, and
allowed code reviews and automated tests of macros, at the cost of requiring
review and a production push to deploy macro changes.

In 2018, the content zones feature was dropped. This was part of an effort
to focus MDN Web Docs on common web platform technologies, and away from
Mozilla-specific documentation. The sub-navigation feature was dropped.

In 2019, the KumaScript engine and macros were modernized to use current
features of JavaScript, such as ``async`` / ``await``, rather than
libraries common in 2011. The API was also unified, so that both previews
and standard renders required a ``POST``.

.. _CSV: https://en.wikipedia.org/wiki/Concurrent_Versions_System
.. _MediaWiki: https://en.wikipedia.org/wiki/MediaWiki
.. _`MediaWiki Markup`: https://en.wikipedia.org/wiki/MediaWiki#Markup
.. _`MindTouch DekiWiki`: https://en.wikipedia.org/wiki/MindTouch
.. _Kitsune: https://github.com/mozilla/kitsune
.. _support.mozilla.org: https://support.mozilla.org/en-US/
.. _KumaScript: https://github.com/mdn/kumascript
.. _`macros folder in the KumaScript repository`: https://github.com/mdn/kumascript/commits/master/macros
.. _`mdn/archived_kumascript`: https://github.com/mdn/archived_kumascript

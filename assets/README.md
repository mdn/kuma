Kuma Assets
===========
This folder contains front-end assets for developer.mozilla.org.

In production, they are collected to ``/static``, processed to add
a hash of the contents to the name, and served to users.
In development, some may be served from this folder, to speed up
development. See
[Building, collecting, and serving assets](https://kuma.readthedocs.io/en/latest/assets.html)
for the details.

Here are the subfolders:

* `build`: (TODO) Output of ``gulp`` and ``make compilejsi18n``, copied to
  ``static/build``.
* `ckeditor4`: (TODO) The source and build folders for CKEditor.
  ``ckeditor/build`` is copied to ``static/js/libs/ckeditor/build``.
* `dist`: (TODO) Output of the ``webpack`` process, copied to ``static/dist``.
* `legacy`: These files are no longer served to users, and are candidates
  for deletion.
* `lib`: (TODO) Third-party libraries that are served to users.
* `pipeline`: (TODO) Input of the ``gulp`` process. It should be possible to
  convert these to ``webpack`` some day.
* `reference`: These files are related to assets, but are not part of an
  automated build process, and are not served to users.
* `src`: (TODO) Input for the ``webpack`` process.
* `static`: These files are copied to ``/static``. Small files (under 32
  kilobytes) in a folder called `embed` (such as `static/img/embed`) may be
  inlined as ``data:`` by
  [django-pipeline](https://django-pipeline.readthedocs.io/en/latest/configuration.html#embedding-fonts-and-images).

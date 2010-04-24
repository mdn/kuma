=================
Discussion Forums
=================

The "normal," discussion forums, like Contributors and Off-Topic, run
through this app. If you're looking for the Support forums, see the Support
app. This is not the app you're looking for. You can go about your business.
Move along.


TODO
====

There's still a lot to do. Here's a partial list:

* Hook up Django admin for this app.

* Come up with some kind of ACL system to restrict access both to the admin
  area and to moderation functions.

* Create a thread and its first post at the same time.

* When creating a new post in a thread, update the ``last_post`` key for
  the thread.

* Implement nice, useful forms.

* Implement better security. Right now it's nonexistent. Spoofing another
  user should be impossible.

* Figure out what's up with cache-machine, and why new threads appear to have
  no posts/replies at first.

* Probably need to stop using ``forms.ModelForm``, at least/especially for
  the new-thread form. But hey, they work for stubs.

* TEST.

* Test some more.

* Keep testing.

* Pretty everything up.

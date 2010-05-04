def test_new_post_updates_thread():
    """Saving a new post in a thread should update the last_post key in
    that thread to point to the new post."""
    pass


def test_update_post_does_not_update_thread():
    """Updating/saving an old post in a thread should _not_ update the
    last_post key in that thread."""
    pass


def test_replies_count():
    """The Thread.replies value should be one less than the number of
    posts in the thread."""
    pass

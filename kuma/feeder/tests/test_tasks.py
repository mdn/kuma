from unittest import mock

from ..tasks import update_feeds


@mock.patch("kuma.feeder.tasks.utils_update_feeds")
def test_update_feeds(mock_update):
    """The update_feeds task calls the update_feeds utility function."""
    update_feeds()
    assert mock_update.called

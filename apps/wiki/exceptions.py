class UniqueCollision(Exception):
    """An attempt to create two pages with the same unique metadata"""
    def __init__(self, existing):
        self.existing = existing


class SlugCollision(UniqueCollision):
    """An attempt to create two pages of the same slug in one locale"""


class DocumentRenderingInProgress(Exception):
    """An attempt to render a page while a rendering is already in progress is
    disallowed."""


class DocumentRenderedContentNotAvailable(Exception):
    """No rendered content available, and an attempt to render on the spot was
    denied. So, the view should fall back to presenting raw content for now."""

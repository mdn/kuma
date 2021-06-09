from datetime import datetime

from django.utils.text import slugify

from kuma.core.tests import get_user

from ..models import Document, Revision


# Model makers. These make it clearer and more concise to create objects in
# test cases. They allow the significant attribute values to stand out rather
# than being hidden amongst the values needed merely to get the model to
# validate.


def document(save=False, **kwargs):
    """Return an empty document with enough stuff filled out that it can be
    saved."""
    defaults = {"title": datetime.now(), "is_redirect": 0}
    defaults.update(kwargs)
    if "slug" not in kwargs:
        defaults["slug"] = slugify(defaults["title"])
    d = Document(**defaults)
    if save:
        d.save()
    return d


def revision(save=False, **kwargs):
    """Return an empty revision with enough stuff filled out that it can be
    saved.

    Revision's is_approved=False unless you specify otherwise.

    Requires a users fixture if no creator is provided.

    """
    doc = None
    if "document" not in kwargs:
        doc = document(save=True)
    else:
        doc = kwargs["document"]

    defaults = {
        "summary": "Some summary",
        "content": "Some content",
        "comment": "Some comment",
        "creator": kwargs.get("creator") or get_user(),
        "document": doc,
        "tags": '"some", "tags"',
        "toc_depth": 1,
    }

    defaults.update(kwargs)

    rev = Revision(**defaults)
    if save:
        rev.save()
    return rev

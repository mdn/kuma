from django.shortcuts import get_object_or_404

import jingo

from .models import Document


#log = logging.getLogger('k.wiki')


def document(request, document_slug):
    """View a wiki document."""
    # This may change depending on how we decide to structure
    # the url and handle locales.
    doc = get_object_or_404(Document, title=document_slug.replace('+', ' '))
    return jingo.render(request, 'wiki/document.html',
                        {'document': doc})

import jingo


def document(request, document_id):
    """View a wiki document."""
    return jingo.render(request, 'wiki/document.html',
                        {'document': None})

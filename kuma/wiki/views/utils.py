# -*- coding: utf-8 -*-


import hashlib


def split_slug(slug):
    """
    Utility function to do basic slug splitting
    """
    slug_split = slug.split('/')
    length = len(slug_split)
    root = None

    seo_root = ''
    bad_seo_roots = ['Web']

    if length > 1:
        root = slug_split[0]

        if root in bad_seo_roots:
            if length > 2:
                seo_root = root + '/' + slug_split[1]
        else:
            seo_root = root

    specific = slug_split.pop()

    parent = '/'.join(slug_split)

    return {                         # with this given: "some/kind/of/Path"
        'specific': specific,        # 'Path'
        'parent': parent,            # 'some/kind/of'
        'full': slug,                # 'some/kind/of/Path'
        'parent_split': slug_split,  # ['some', 'kind', 'of']
        'length': length,            # 4
        'root': root,                # 'some'
        'seo_root': seo_root,        # 'some'
    }


def document_form_initial(document):
    """
    Return a dict with the document data pertinent for the form.
    """
    return {
        'title': document.title,
        'slug': document.slug,
        'is_localizable': document.is_localizable,
        'tags': list(document.tags.names())
    }


def calculate_etag(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

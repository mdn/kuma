from django_jinja import library


@library.global_function
@library.render_with('landing/newsfeed.html')
def newsfeed(entries, section_headers=False):
    """Landing page news feed."""
    return {'updates': entries, 'section_headers': section_headers}

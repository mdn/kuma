from jingo import register


@register.inclusion_tag('landing/newsfeed.html')
def newsfeed(entries, section_headers=False):
    """Landing page news feed."""
    return {'updates': entries, 'section_headers': section_headers}

from django.http import HttpResponseRedirect, Http404
from django.views.decorators.cache import cache_page

from inproduct.models import Redirect
from sumo.helpers import urlparams


@cache_page(24 * 60 * 60)  # 24 hours.
def redirect(request, product, version, platform, locale, topic=None):
    """Redirect in-product URLs to the right place."""
    redirects = Redirect.objects.all()

    # In order from least to most important.
    parts = ('locale', 'product', 'version', 'platform', 'topic')

    # First we remove any redirects that explicitly don't match. Do this in
    # Python to avoid an explosion of cache use.
    t = topic if topic else ''

    def f(redirect):
        matches = (
            redirect.product.lower() in (product.lower(), ''),
            redirect.version.lower() in (version.lower(), ''),
            redirect.platform.lower() in (platform.lower(), ''),
            redirect.locale.lower() in (locale.lower(), ''),
            redirect.topic.lower() == t.lower(),
        )
        return all(matches)

    redirects = filter(f, redirects)

    # Assign a ordinal (score) to each redirect based on how specific it is,
    # then order by score descending.
    #
    # Scores are weighted by powers of 2 so that specifying the most important
    # field (i.e. topic) outweighs specifying all 4 other fields. This means
    # we should find the correct match faster in most common cases.
    # For example, if you have two redirects that have topic='foo', and one
    # of them also has platform='mac', and one with platform='win', they'll
    # sort like:
    #   24, Redirect(topic='foo', platform='mac')
    #   16, Redirect(topic='foo')
    #   8,  Redirect(platform='win')
    # Macs going to 'foo' will will hit the first redirect. Everyone else
    # going to 'foo' will hit the second. (Windows users going to 'foo' would
    # never match Redirect(platform='win') but if it sorted higher, it would
    # take longer to get there.)
    def ordinal(redirect):
        score = 0
        for i, part in enumerate(parts):
            if getattr(redirect, part) != '':
                score += 1 << i
        return score, redirect

    ordered = map(ordinal, redirects)
    ordered.sort(key=lambda x: x[0], reverse=True)

    # A redirect matches if all its fields match. A field matches if it is
    # blank or matches the input.
    def matches(redirect, **kw):
        for part in parts:
            attr = getattr(redirect, part)
            if attr != '':
                v = kw[part] if kw[part] else ''
                if attr.lower() != v.lower():
                    return False
        return True

    # As soon as we've found a match, that's the best one.
    destination = None
    for score, redirect in ordered:
        if matches(redirect, product=product, version=version,
                   platform=platform, locale=locale, topic=topic):
            destination = redirect
            break

    # Oh noes! We didn't find a target.
    if not destination:
        raise Http404

    # If the target starts with HTTP, we don't add a locale or query string
    # params.
    if destination.target.startswith('http'):
        target = destination.target
    else:
        params = {'as': 'u'}
        if hasattr(request, 'eu_build'):
            params['eu'] = 1
        target = u'/%s/%s' % (locale, destination.target.lstrip('/'))
        target = urlparams(target, **params)

    # 302 because these can change over time.
    return HttpResponseRedirect(target)

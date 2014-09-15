# django never_cache isn't as thorough as we might like
# http://stackoverflow.com/a/2095648/571420
# http://stackoverflow.com/a/2068407/571420
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching_FAQ
def never_cache(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        resp = view_func(request, *args, **kwargs)

        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'

        return resp

    return _wrapped_view_func

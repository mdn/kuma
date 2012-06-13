from waffle import flag_is_active

from wiki import ReadOnlyException


def check_readonly(view):
    def _check_readonly(request, *args, **kwargs):
        if not flag_is_active(request, 'kumaediting'):
            raise ReadOnlyException("kumaediting")
        elif flag_is_active(request, 'kumabanned'):
            raise ReadOnlyException("kumabanned")

        return view(request, *args, **kwargs)
    return _check_readonly

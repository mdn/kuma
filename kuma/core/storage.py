from urlparse import urljoin

from localdevstorage.http import HttpStorage
from django.utils.encoding import filepath_to_uri


class KumaHttpStorage(HttpStorage):

    def _url(self, name):
        # temporary fix until this is merged:
        #   https://github.com/piquadrat/django-localdevstorage/pull/8
        # this fixes a wrong URL joining that would ignore the base URL path
        # of MEDIA_URL here-----v
        return urljoin(self.base_url, filepath_to_uri(name))

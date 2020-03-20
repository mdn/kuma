import logging

from elasticsearch.exceptions import ConnectionError


log = logging.getLogger("kuma.search.decorators")


def requires_good_connection(fun):
    """Decorator that logs an error on connection issues

    9 out of 10 doctors say that connection errors are usually because
    ES_URLS is set wrong. This catches those errors and helps you out
    with fixing it.

    """

    def _requires_good_connection(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except ConnectionError:
            log.error(
                "Either your ElasticSearch process is not quite "
                "ready to rumble, is not running at all, or ES_URLS"
                "is set wrong in your .env file."
            )

    return _requires_good_connection

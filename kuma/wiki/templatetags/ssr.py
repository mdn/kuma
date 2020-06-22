import json
import os
from functools import lru_cache

import requests
import requests.exceptions
from django.conf import settings
from django_jinja import library


@lru_cache()
def get_localization_data(locale):
    """
    Read the frontend string catalog for the specified locale, parse
    it as JSON, and return the resulting dict. The returned values
    are cached so that we don't have to read files all the time.
    """
    path = os.path.join(settings.BASE_DIR, "static", "jsi18n", locale, "react.json")
    with open(path, "r") as f:
        return json.load(f)


@library.global_function
def render_react(component_name, locale, url, document_data, ssr=True):
    """
    Render a script tag to define the data and any other HTML tags needed
    to enable the display of a React-based UI. By default, this does
    server side rendering, falling back to client-side rendering if
    the SSR attempt fails. Pass False as the second argument to do
    client-side rendering unconditionally.

    Note that we are not defining a generic Jinja template tag here.
    The code in this file is specific to Kuma's React-based UI.
    """
    localization_data = get_localization_data(locale)

    data = {
        "locale": locale,
        "stringCatalog": localization_data["catalog"],
        "pluralExpression": localization_data["plural"],
        "url": url,
        "documentData": document_data,
    }
    if ssr:
        return server_side_render(component_name, data)
    else:
        return client_side_render(component_name, data)


def _render(component_name, html, script, needs_serialization=False):
    """A utility function used by both client side and server side rendering.
    Returns a string that includes the specified HTML and a serialized
    form of the state dict, in the format expected by the client-side code
    in kuma/javascript/src/index.jsx.
    """
    if needs_serialization:
        assert isinstance(script, dict), type(script)
        script = json.dumps(script).replace("</", "<\\/")
    else:
        script = "JSON.parse({})".format(script)

    return (
        '<div id="react-container" data-component-name="{}">{}</div>\n'
        "<script>window._react_data = {};</script>\n"
    ).format(component_name, html, script)


def client_side_render(component_name, data):
    """
    Output an empty <div> and a script with complete state so that
    the UI can be rendered on the client-side.
    """
    return _render(component_name, "", data, needs_serialization=True)


def server_side_render(component_name, data):
    """
    Pre-render the React UI to HTML and output it in a <div>, and then
    also pass the necessary serialized state in a <script> so that
    React on the client side can sync itself with the pre-rendred HTML.

    If any exceptions are thrown during the server-side rendering, we
    fall back to client-side rendering instead.
    """
    url = "{}/{}".format(settings.SSR_URL, component_name)
    timeout = settings.SSR_TIMEOUT
    # Try server side rendering
    try:
        # POST the document data as JSON to the SSR server and we
        # should get HTML text (encoded as plain text) in the body
        # of the response
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data).encode("utf8"),
            timeout=timeout,
        )

        # Even though we've got fully rendered HTML now, we still need to
        # send the document data along with it so that React can sync its
        # state on the client side with what is in the HTML. When rendering
        # a document page, the data includes long strings of HTML that
        # we can get away without duplicating. So as an optimization when
        # component_name is "document", we're going to make a copy of the
        # data (because the original belongs to our caller) and delete those
        # strings from the copy.
        #
        # WARNING: This optimization can save 20kb in data transfer
        # for typical pages, but it requires us to be very careful on
        # the frontend. If any components render conditionally based on
        # the state of bodyHTML, tocHTML or quickLinkHTML, then they will
        # render differently on the client than during SSR, and the hydrate
        # will not just work cleanly, and those components will re-render
        # with empty strings. This has already caused Bug 1558308, and
        # I've commented it out because the benefit in file size doesn't
        # seem worth the risk of client-side bugs.
        #
        # As an alternative, it ought to be possible to extract the HTML
        # strings from the SSR'ed document and rebuild the document object
        # on the client right before we call hydrate(). So if you uncomment
        # the lines below, you should also edit kuma/javascript/src/index.jsx
        # to extract the HTML from the document as well.
        #
        # if component_name == 'document':
        #     data = data.copy()
        #     data['documentData'] = data['documentData'].copy()
        #     data['documentData'].update(bodyHTML='',
        #                                 tocHTML='',
        #                                 quickLinksHTML='')
        response.raise_for_status()
        result = response.json()
        return _render(component_name, result["html"], result["script"])

    except requests.exceptions.RequestException as exception:
        print(f"{exception.__class__} error contacting SSR server.")
        print("Falling back to client side rendering.")
        return client_side_render(component_name, data)

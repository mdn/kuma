// @flow
import React from 'react';
import ReactDOM from 'react-dom';

import App from './app.jsx';
import { localize } from './l10n.js';

let container = document.getElementById('react-container');
if (container) {
    // The HTML page that loads this code is expected to have an inline
    // script that sets this window._document_data property to an object
    // with all the data needed to hydrate or render the UI.
    let data = window._react_data;

    // Remove the global reference to this data object so that it can
    // be garbage collected once it is no longer in use.
    window._react_data = null; // eslint-disable-line camelcase

    // Store the string catalog so that l10n.gettext() can do translations
    localize(data.requestData.locale, data.stringCatalog, data.pluralFunction);

    // This is the React UI for a page of documentation
    let app = <App documentData={data.documentData} />;

    if (container.firstElementChild) {
        // If the container element is not empty, then it was presumably
        // rendered on the server, and we just need to hydrate it now.
        ReactDOM.hydrate(app, container);
    } else {
        // Otherwise, if the container is empty, then we need to do a full
        // client-side render. The goal is that pages should always be
        // server-side rendered when first loaded (for speed and SEO). But
        // this is here for robustness in case there are errors during
        // server side rendering.
        ReactDOM.render(app, container);
    }

    // Finally, here is some other miscellaneous code that we need to run.
    // The idea is that this is code need to make the non-React parts of
    // the UX work correctly. If we end up with more than a couple of things
    // here we should refactor them into a separate module

    // An event handler to make the language selector menu
    // in the footer work correctly.
    // See also kuma/static/js/main.js where similar code appears ot
    // make the menu work on the wiki domain
    for (let menu of document.querySelectorAll('select.autosubmit')) {
        menu.addEventListener('change', function() {
            this.form.submit();
        });
    }
}

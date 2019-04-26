// @flow
import React from 'react';
import ReactDOM from 'react-dom';

import DocumentProvider from './document-provider.jsx';
import Page from './page.jsx';
import UserProvider from './user-provider.jsx';

let container = document.getElementById('react-container');

if (container) {
    // The HTML page that loads this code is expected to have an inline
    // script that sets this window._document_data property to an object
    // with all the data needed to hydrate or render the UI.
    let data = window._document_data;

    // Remove the global reference to this data object so that it can
    // be garbage collected once it is no longer in use.
    window._document_data = null; // eslint-disable-line camelcase

    // This is the React UI for a page of documentation
    let page = (
        <DocumentProvider initialDocumentData={data}>
            <UserProvider>
                <Page />
            </UserProvider>
        </DocumentProvider>
    );

    if (container.firstElementChild) {
        // If the container element is not empty, then it was presumably
        // rendered on the server, and we just need to hydrate it now.
        ReactDOM.hydrate(page, container);
    } else {
        // Otherwise, if the container is empty, then we need to do a full
        // client-side render. The goal is that pages should always be
        // server-side rendered when first loaded (for speed and SEO). But
        // this is here for robustness in case there are errors during
        // server side rendering.
        ReactDOM.render(page, container);
    }
}

// @flow
import React from 'react';
import ReactDOM from 'react-dom';

import CurrentUser from './current-user.jsx';
import DocumentProvider from './document-provider.jsx';
import Page from './page.jsx';

let container = document.getElementById('react-container');

if (container) {
    let script = container.firstElementChild;
    if (script && script instanceof HTMLScriptElement) {
        // We expect the script to contain a base64-encoded JSON blob
        // that contains all the content of this document
        let data = JSON.parse(atob(script.text));
        ReactDOM.render(
            <DocumentProvider initialDocumentData={data}>
                <CurrentUser.Provider>
                    <Page />
                </CurrentUser.Provider>
            </DocumentProvider>,
            container
        );
    }
}

import React from 'react';
import { renderToString } from 'react-dom/server';

import CurrentUser from './current-user.jsx';
import DocumentProvider from './document-provider.jsx';
import Page from './page.jsx';

/*
 * This function performs server-side rendering of our UI, given
 * a JSON object of document data. It is used by ../ssr-server.js
 */
export default function ssr(data) {
    return renderToString(
        <DocumentProvider initialDocumentData={data}>
            <CurrentUser.Provider>
                <Page />
            </CurrentUser.Provider>
        </DocumentProvider>
    );
}

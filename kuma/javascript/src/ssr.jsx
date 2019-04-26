import React from 'react';
import { renderToString } from 'react-dom/server';

import DocumentProvider from './document-provider.jsx';
import Page from './page.jsx';
import UserProvider from './user-provider.jsx';

/*
 * This function performs server-side rendering of our UI, given
 * a JSON object of document data. It is used by ../ssr-server.js
 */
export default function ssr(data) {
    return renderToString(
        <DocumentProvider initialDocumentData={data}>
            <UserProvider>
                <Page />
            </UserProvider>
        </DocumentProvider>
    );
}

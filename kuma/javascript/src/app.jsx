// @flow
import * as React from 'react';

import DocumentProvider from './document-provider.jsx';
import GAProvider from './ga-provider.jsx';
import Page from './page.jsx';
import UserProvider from './user-provider.jsx';

import type DocumentData from './document-provider.jsx';

export default function App(props: { documentData: DocumentData }) {
    return (
        <GAProvider>
            <DocumentProvider initialDocumentData={props.documentData}>
                <UserProvider>
                    <Page />
                </UserProvider>
            </DocumentProvider>
        </GAProvider>
    );
}

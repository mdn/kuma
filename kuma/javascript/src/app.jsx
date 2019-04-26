// @flow
import * as React from 'react';

import DocumentProvider from './document-provider.jsx';
import Page from './page.jsx';
import UserProvider from './user-provider.jsx';

import type DocumentData from './document-provider.jsx';

export default function App(props: { initialDocumentData: DocumentData }) {
    return (
        <DocumentProvider initialDocumentData={props.initialDocumentData}>
            <UserProvider>
                <Page />
            </UserProvider>
        </DocumentProvider>
    );
}

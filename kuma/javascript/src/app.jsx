// @flow
import * as React from 'react';

import DocumentProvider from './document-provider.jsx';
import GAProvider from './ga-provider.jsx';
import LocaleProvider from './locale-provider.jsx';
import Page from './page.jsx';
import UserProvider from './user-provider.jsx';

import type DocumentData from './document-provider.jsx';
type RequestData = {
    locale: string
};
type Props = { documentData: DocumentData, requestData: RequestData };

export default function App(props: Props) {
    return (
        <GAProvider>
            <LocaleProvider locale={props.requestData.locale}>
                <DocumentProvider initialDocumentData={props.documentData}>
                    <UserProvider>
                        <Page />
                    </UserProvider>
                </DocumentProvider>
            </LocaleProvider>
        </GAProvider>
    );
}

//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import DocumentProvider from './document-provider.jsx';
import { fakeDocumentData } from './document-provider.test.js';
import Page from './page.jsx';

test('Page snapshot', () => {
    const page = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <Page />
        </DocumentProvider>
    );
    expect(page.toJSON()).toMatchSnapshot();
});

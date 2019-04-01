//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import DocumentProvider from '../document-provider.jsx';
import { fakeDocumentData } from '../document-provider.test.js';
import Header from './header.jsx';

test('Header snapshot', () => {
    const header = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <Header />
        </DocumentProvider>
    );
    expect(header.toJSON()).toMatchSnapshot();
});

//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import DocumentProvider from '../document-provider.jsx';
import { fakeDocumentData } from '../document-provider.test.js';
import Search from './search.jsx';

test('Search snapshot', () => {
    const search = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <Search />
        </DocumentProvider>
    );
    expect(search.toJSON()).toMatchSnapshot();
});

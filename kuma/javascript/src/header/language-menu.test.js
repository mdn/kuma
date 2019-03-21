//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import DocumentProvider from '../document-provider.jsx';
import { fakeDocumentData } from '../document-provider.test.js';
import LanguageMenu from './language-menu.jsx';

test('LanguageMenu snapshot', () => {
    const page = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <LanguageMenu />
        </DocumentProvider>
    );
    expect(page.toJSON()).toMatchSnapshot();
});

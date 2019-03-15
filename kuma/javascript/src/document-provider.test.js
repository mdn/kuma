//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import DocumentProvider from './document-provider.jsx';

export const fakeDocumentData = {
    locale: 'en-US',
    slug: 'test',
    id: 42,
    title: '[fake document title]',
    summary: '[fake document summary]',
    absoluteURL: '[fake absolute url]',
    redirectURL: '',
    editURL: '[fake edit url]',
    bodyHTML: '[fake body HTML]',
    quickLinksHTML: '[fake quicklinks HTML]',
    tocHTML: '[fake TOC HTML]',
    parents: [
        {
            url: '[fake grandparent url]',
            title: '[fake grandparent title]'
        },
        {
            url: '[fake parent url]',
            title: '[fake parent title]'
        }
    ],
    translations: [
        {
            locale: 'es',
            url: '[fake spanish url]',
            title: '[fake spanish translation]'
        }
    ]
};

describe('DocumentProvider', () => {
    // TODO: DocumentProvider also implements client-side navigation.
    // I haven't figured out how to write a test for that yet, however.
    test('context works', () => {
        const C = DocumentProvider.context.Consumer;
        const contextConsumer = jest.fn();

        create(
            <DocumentProvider initialDocumentData={fakeDocumentData}>
                <C>{contextConsumer}</C>
            </DocumentProvider>
        );

        expect(contextConsumer.mock.calls.length).toBe(1);
        expect(contextConsumer.mock.calls[0][0]).toEqual(fakeDocumentData);
    });
});

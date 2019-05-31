//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import Document from './document.jsx';

export const fakeDocumentData = {
    locale: 'en-US',
    slug: 'test',
    enSlug: 'fake/en/slug',
    id: 42,
    title: '[fake document title]',
    summary: '[fake document summary]',
    language: 'English (US)',
    hrefLang: 'en',
    absoluteURL: '[fake absolute url]',
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
            language: 'Español',
            hrefLang: 'es',
            localizedLanguage: 'Spanish',
            url: '[fake spanish url]',
            title: '[fake spanish translation]'
        }
    ],
    contributors: ['mike', 'ike'],
    lastModified: '2019-01-02T03:04:05Z',
    lastModifiedBy: 'ike'
};

test('Document snapshot', () => {
    const document = create(<Document data={fakeDocumentData} />);
    expect(document.toJSON()).toMatchSnapshot();
});

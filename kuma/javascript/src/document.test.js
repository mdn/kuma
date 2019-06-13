//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import Article from './article.jsx';
import Document, { Breadcrumbs, DocumentRoute, Sidebar } from './document.jsx';
import Header from './header/header.jsx';
import TaskCompletionSurvey from './task-completion-survey.jsx';
import Titlebar from './titlebar.jsx';

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

describe('Document component renders all of its parts', () => {
    const document = create(<Document data={fakeDocumentData} />);
    const snapshot = JSON.stringify(document.toJSON());
    const root = document.root;

    // The document should have exactly one Header
    test('header', () => {
        const headers = root.findAllByType(Header);
        expect(headers.length).toBe(1);
    });

    // The document has a task completion survey component, even
    // if it does not render anything
    test('task completion survey', () => {
        expect(root.findAllByType(TaskCompletionSurvey).length).toBe(1);
    });

    // The document should have one Titlebar, with the document title.
    test('titlebar', () => {
        const titlebars = root.findAllByType(Titlebar);
        expect(titlebars.length).toBe(1);
        expect(titlebars[0].props.title).toBe(fakeDocumentData.title);
    });

    // The document has one breadcrumbs element with links to the
    // ancestor elements
    test('breadcrumbs', () => {
        const breadcrumbs = root.findAllByType(Breadcrumbs);
        expect(breadcrumbs.length).toBe(1);
        const links = breadcrumbs[0].findAllByType('a');
        for (let i = 0; i < fakeDocumentData.parents.length; i++) {
            let parent = fakeDocumentData.parents[i];
            let link = links[i];
            expect(link.props.href).toBe(parent.url);
            expect(link.children[0].children[0]).toBe(parent.title);
        }
    });

    // The document has one sidebar element
    test('sidebar', () => {
        const sidebars = root.findAllByType(Sidebar);
        expect(sidebars.length).toBe(1);
    });

    // And one article element
    test('article', () => {
        const articles = root.findAllByType(Article);
        expect(articles.length).toBe(1);
    });

    // And make sure that our various strings of HTML appear in the document
    test('html strings', () => {
        expect(snapshot).toContain(fakeDocumentData.tocHTML);
        expect(snapshot).toContain(fakeDocumentData.quickLinksHTML);
        expect(snapshot).toContain(fakeDocumentData.bodyHTML);
    });

    test('contributor names appear', () => {
        for (let c of fakeDocumentData.contributors) {
            expect(snapshot).toContain(c);
        }
    });
});

describe('DocumentRoute', () => {
    const route = new DocumentRoute('en-US');

    test('getComponent()', () => {
        expect(route.getComponent()).toBe(Document);
    });

    test('matches well-formed URLs and paths, extracts slug', () => {
        expect(route.match('https://mdn.dev/en-US/docs/slug')).toEqual({
            locale: 'en-US',
            slug: 'slug'
        });
        expect(route.match('/en-US/docs/slug')).toEqual({
            locale: 'en-US',
            slug: 'slug'
        });
        expect(route.match('en-US/docs/slug')).toEqual({
            locale: 'en-US',
            slug: 'slug'
        });

        expect(route.match('/en-US/docs/Web/API/Canvas')).toEqual({
            locale: 'en-US',
            slug: 'Web/API/Canvas'
        });
    });

    test('does not match wrong locale', () => {
        expect(route.match('/es/docs/slug')).toBe(null);
        expect(route.match('https://mdn.dev/fr/docs/slug')).toBe(null);
        expect(route.match('//docs/slug')).toBe(null);
    });

    test('does not match urls without /docs/', () => {
        expect(route.match('/en-US/ducks/slug')).toBe(null);
        expect(route.match('https://mdn.dev/en-US/ducks/slug')).toBe(null);
    });

    test('fetch() method fetches the right data', done => {
        // In this test we want to verify that UserProvider is
        // fetching user data from an API. So we need to mock fetch().
        global.fetch = jest.fn(() => {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ documentData: fakeDocumentData })
            });
        });

        route.fetch({ locale: 'en-US', slug: 'Web/API/Canvas' }).then(() => {
            expect(global.fetch).toHaveBeenCalledTimes(1);
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/v1/doc/en-US/Web/API/Canvas'
            );
            done();
        });
    });
    test('fetch() method falls back to en-US for untranslated docs', done => {
        // In this test we want to verify that UserProvider is
        // fetching user data from an API. So we need to mock fetch().
        global.fetch = jest.fn(url => {
            return Promise.resolve({
                ok: url.includes('en-US'),
                json: () => Promise.resolve({ documentData: fakeDocumentData })
            });
        });

        // fetch() falls back to the english locale if it can't find
        // a document in the requested language
        const route2 = new DocumentRoute('untranslated');

        route2
            .fetch({ locale: 'untranslated', slug: 'Web/API/Canvas' })
            .then(() => {
                expect(global.fetch).toHaveBeenCalledTimes(2);
                expect(global.fetch.mock.calls[0][0]).toBe(
                    '/api/v1/doc/untranslated/Web/API/Canvas'
                );
                expect(global.fetch.mock.calls[1][0]).toBe(
                    '/api/v1/doc/en-US/Web/API/Canvas'
                );
                done();
            });
    });

    test('getTitle() returns the fetched document title', () => {
        expect(
            route.getTitle({ locale: 'en-US', slug: 'slug' }, fakeDocumentData)
        ).toBe(fakeDocumentData.title);
    });

    test('analyticsHook() calls ga with enSlug', () => {
        let ga = jest.fn();
        route.analyticsHook(
            ga,
            { locale: 'en-US', slug: 'slug' },
            fakeDocumentData
        );
        expect(ga.mock.calls[0][0]).toBe('set');
        expect(ga.mock.calls[0][1]).toBe('dimension17');
        expect(ga.mock.calls[0][2]).toBe(fakeDocumentData.enSlug);
    });
});

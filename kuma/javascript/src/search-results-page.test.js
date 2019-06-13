//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import Header from './header/header.jsx';
import SearchResultsPage, { SearchRoute } from './search-results-page.jsx';
import Titlebar from './titlebar.jsx';
import type { SearchResults } from './search-results-page.jsx';

const fakeSearchResults: SearchResults = [
    {
        slug: 'slug1',
        title: 'title1',
        summary: 'summary1',
        tags: ['tag1.1', 'tag1.2']
    },
    {
        slug: 'slug2',
        title: 'title2',
        summary: 'summary2',
        tags: ['tag2.1', 'tag2.2']
    }
];

describe('SearchResultsPage component', () => {
    const page = create(
        <SearchResultsPage locale="en-US" query="qq" data={fakeSearchResults} />
    );
    const snapshot = JSON.stringify(page.toJSON());
    const root = page.root;

    // The page should have exactly one Header
    test('header', () => {
        const headers = root.findAllByType(Header);
        expect(headers.length).toBe(1);
    });

    // The page should one Titlebar, with the expected title
    test('titlebar', () => {
        const titlebars = root.findAllByType(Titlebar);
        expect(titlebars.length).toBe(1);
        expect(titlebars[0].props.title).toBe('Results: qq');
    });

    // The final form of the search results page isn't decided yet
    // but we expect the strings of the fake search data to appear
    // in the page somewhere
    test('results', () => {
        for (const hit of fakeSearchResults) {
            expect(snapshot).toContain(hit.title);
            expect(snapshot).toContain(hit.summary);
            expect(snapshot).toContain(hit.slug);
        }
    });
});

describe('SearchRoute', () => {
    const route = new SearchRoute('en-US');
    test('getComponent()', () => {
        expect(route.getComponent()).toBe(SearchResultsPage);
    });

    test('match() extracts the query string', () => {
        expect(route.match('/en-US/search?q=qq')).toEqual({
            locale: 'en-US',
            query: 'qq'
        });
        expect(route.match('/en-US/search?foo=bar&q=qq')).toEqual({
            locale: 'en-US',
            query: 'qq'
        });
        expect(route.match('http://mdn.dev/en-US/search?q=qq')).toEqual({
            locale: 'en-US',
            query: 'qq'
        });
        expect(
            route.match('https://mdn.dev/en-US/search?foo=bar&q=qq')
        ).toEqual({
            locale: 'en-US',
            query: 'qq'
        });
    });

    test('match() does not match if locale does not match', () => {
        expect(route.match('/es/search?q=qq')).toBe(null);
        expect(route.match('/fr/search?q=qq')).toBe(null);
    });

    test('match() does not match if no query string', () => {
        expect(route.match('/en-US/search')).toBe(null);
        expect(route.match('/en-US/search?p=qq')).toBe(null);
    });

    test('match() does not match if no /search in URL', () => {
        expect(route.match('/en-US/?q=qq')).toBe(null);
        expect(route.match('/en-US/searching?q=qq')).toBe(null);
    });

    test('fetch() method invokes the search api', done => {
        global.fetch = jest.fn(() => {
            return Promise.resolve({
                ok: true,
                json: () =>
                    Promise.resolve({
                        // ElasticSearch buries the results in layers of
                        // other stuff that we fake out here
                        hits: {
                            hits: fakeSearchResults.map(r => ({ _source: r }))
                        }
                    })
            });
        });

        route.fetch({ locale: 'en-US', query: 'foo bar#' }).then(results => {
            expect(results).toEqual(fakeSearchResults);
            expect(global.fetch.mock.calls[0][0]).toBe(
                '/api/v1/search/en-US?q=foo%20bar%23'
            );
            done();
        });
    });

    test('getTitle()', () => {
        expect(route.getTitle({ locale: '', query: 'qq' })).toBe(
            'Search results for "qq" | MDN'
        );
    });
});

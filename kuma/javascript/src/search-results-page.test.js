//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import Header from './header/header.jsx';
import SearchResultsPage, { SearchRoute } from './search-results-page.jsx';
import Titlebar from './titlebar.jsx';
import type { SearchResults } from './search-results-page.jsx';

const fakeResults = [
    {
        slug: 'slug1',
        title: 'title1',
        summary: 'summary1',
        score: 10,
        excerpts: ['Test <mark>result</mark>', 'Excerpt <mark>2</mark>']
    },
    {
        slug: 'slug2',
        title: 'title2',
        summary: 'summary2',
        score: 5,
        excerpts: []
    }
];

const fakeSearchResults: SearchResults = {
    results: fakeResults,
    error: null
};

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
        for (const hit of fakeResults) {
            expect(snapshot).toContain(hit.title);
            expect(snapshot).toContain(hit.summary);
            expect(snapshot).toContain(hit.slug);
            for (const excerpt of hit.excerpts) {
                expect(snapshot).toContain(excerpt);
            }
        }
    });
});

describe('SearchResultsPage with error', () => {
    const error = new Error('SearchError');

    const page = create(
        <SearchResultsPage
            locale="en-US"
            query="qq"
            data={{ error, results: null }}
        />
    );
    const snapshot = JSON.stringify(page.toJSON());

    test('Page displays error message', () => {
        // The page should contain the error message
        expect(snapshot).toContain(error.toString());
    });
});

describe('SearchResultsPage with no results found', () => {
    const page = create(
        <SearchResultsPage
            locale="en-US"
            query="qq"
            data={{ error: null, results: [] }}
        />
    );
    const snapshot = JSON.stringify(page.toJSON());

    test('Page displays no results message', () => {
        expect(snapshot).toContain('No matching documents found.');
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
                        hits: fakeResults.map(r => ({
                            slug: r.slug,
                            title: r.title,
                            summary: r.summary,
                            score: r.score,
                            excerpts: r.excerpts
                        }))
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

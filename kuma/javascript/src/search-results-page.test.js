//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import Header from './header/header.jsx';
import SearchResultsPage, { SearchRoute } from './search-results-page.jsx';
import Titlebar from './titlebar.jsx';
import type { SearchResultsResponse } from './search-results-page.jsx';

const fakeResults = {
    count: 2,
    documents: [
        {
            slug: 'slug1',
            title: 'title1',
            locale: 'en-US',
            excerpt: 'Test <mark>result</mark> Excerpt <mark>2</mark>'
        },
        {
            slug: 'slug2',
            title: 'title2',
            locale: 'en-US',
            excerpt: 'empty'
        }
    ],
    start: 0,
    end: 10,
    filters: {},
    locale: 'en-US',
    next: null,
    page: 1,
    pages: 0,
    previous: null,
    query: 'q'
};

const fakeEmptyResults = {
    count: 0,
    documents: [],
    start: 0,
    end: 0,
    filters: {},
    locale: 'en-US',
    next: null,
    page: 0,
    pages: 0,
    previous: null,
    query: 'empty'
};

const fakeSearchResults: SearchResultsResponse = {
    results: fakeResults,
    error: null
};

const fakeEmptySearchResults: SearchResultsResponse = {
    results: fakeEmptyResults,
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
        for (const document of fakeResults.documents) {
            expect(snapshot).toContain(document.title);
            expect(snapshot).toContain(document.slug);
            expect(snapshot).toContain(document.excerpt);
        }
    });
});

describe('SearchResultsPage with error', () => {
    const error = new Error('SearchError');

    const data = { error, results: fakeEmptyResults };
    const page = create(
        <SearchResultsPage locale="en-US" query="qq" data={data} />
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
            data={fakeEmptySearchResults}
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
            page: 1,
            query: 'qq'
        });
        expect(route.match('/en-US/search?foo=bar&q=qq')).toEqual({
            locale: 'en-US',
            page: 1,
            query: 'qq'
        });
        expect(route.match('http://mdn.dev/en-US/search?q=qq')).toEqual({
            locale: 'en-US',
            page: 1,
            query: 'qq'
        });
        expect(
            route.match('https://mdn.dev/en-US/search?foo=bar&q=qq')
        ).toEqual({
            locale: 'en-US',
            page: 1,
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
                json: () => Promise.resolve(fakeResults)
            });
        });

        route
            .fetch({ locale: 'en-US', query: 'foo bar#', page: null })
            .then(results => {
                expect(results).toEqual(fakeSearchResults);
                expect(global.fetch.mock.calls[0][0]).toBe(
                    '/api/v1/search/en-US?q=foo%20bar%23&locale=en-US'
                );
                done();
            });
    });

    test('getTitle()', () => {
        expect(route.getTitle({ locale: '', query: 'qq', page: null })).toBe(
            'Search results for "qq" | MDN'
        );
    });
});

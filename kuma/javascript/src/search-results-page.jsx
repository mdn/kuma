// @flow
import * as React from 'react';
import { css } from '@emotion/core';

import { gettext } from './l10n.js';
import Header from './header/header.jsx';
import Titlebar from './titlebar.jsx';

import type Route from './router.jsx';

type SearchResults = Array<{
    slug: string,
    title: string,
    summary: string,
    tags: Array<string>
}>;

const styles = {
    searchResult: css({
        padding: '8px 24px',
        maxWidth: 600,
        marginLeft: 'auto',
        marginRight: 'auto'
    }),
    searchResultLink: css({}),
    searchResultSummary: css({})
};

type Props = {
    locale: string,
    query: string,
    data: ?SearchResults
};

export default function SearchResultsPage({ locale, query, data }: Props) {
    return (
        <>
            <Header />
            <Titlebar title={`${gettext('Search Results')}: ${query}`} />
            {data &&
                data.map(hit => {
                    let url = `/${locale}/docs/${hit.slug}`;
                    return (
                        <div css={styles.searchResult} key={hit.slug}>
                            <a css={styles.searchResultLink} href={url}>
                                {hit.title}
                            </a>
                            <div css={styles.searchResultSummary}>
                                {hit.summary}
                            </div>
                        </div>
                    );
                })}
        </>
    );
}

// In order to use new URL() with relative URLs, we need an absolute base
// URL. If we're running in the browser we can use our current page URL.
// But if we're doing SSR, we just have to make something up.
const BASEURL =
    typeof window !== 'undefined' && window.location
        ? window.location.origin
        : 'http://ssr.hack';

type SearchRouteMatchData = {
    locale: string,
    query: string
};

// This Route object tells the Router component how to convert
// search URLs into SearchResultPage components. See router.jsx.
export const SearchRoute: Route = {
    component: SearchResultsPage,

    match(url: string): ?SearchRouteMatchData {
        let parsed = new URL(url, BASEURL);
        let path = parsed.pathname;
        let m = path.match(/^\/([^/]+)\/search$/);
        if (m && m[1]) {
            let q = parsed.searchParams.get('q');
            if (q) {
                return {
                    locale: m[1],
                    query: q
                };
            }
        }

        // If the path didn't match or we didn't find a query,
        // we can't handle this URL
        return null;
    },

    fetch({ locale, query }: SearchRouteMatchData): Promise<SearchResults> {
        return fetch(`/api/v1/search/${locale}?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(results => results && results.hits.hits.map(h => h._source));
    },

    title(matchedData): string {
        return `Search results for: ${matchedData.query} | MDN`;
    }
};

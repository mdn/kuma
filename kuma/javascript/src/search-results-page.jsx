// @flow
import * as React from 'react';
import { css } from '@emotion/core';

import { gettext } from './l10n.js';
import Header from './header/header.jsx';
import Route from './route.js';
import Titlebar from './titlebar.jsx';

type SearchRouteParams = {
    locale: string,
    query: string
};

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
                    // TODO: This design is a placeholder only.
                    // We should display the link URL like the wiki site does.
                    // And maybe try displaying tags as well.
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

// This Route subclass tells the Router component how to convert
// search URLs into SearchResultPage components. See route.js and router.jsx.
export class SearchRoute extends Route<SearchRouteParams, SearchResults> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return SearchResultsPage;
    }

    match(url: string): ?SearchRouteParams {
        let parsed = new URL(url, BASEURL);
        let path = parsed.pathname;
        let q = parsed.searchParams.get('q');

        if (path !== `/${this.locale}/search` || !q) {
            return null;
        }

        return { locale: this.locale, query: q };
    }

    // TODO:
    // Need to think through error handling here. If response.ok is false
    // what do we do?  If the promise is rejected the router will
    // fall back to a regular full document load, but that is likely to
    // make the same query and fail in the same way possibly causing
    // an infinite loop!
    //
    // Perhaps we need to define some different types of errors that
    // we can throw. One would cause a full document load rather than
    // client side nav. Another type of error would display some kind of
    // client-side "oops" page. Does the router need to be able to display
    // error messages?
    //
    // Maybe this route shouldn't have a fetch method at all. Better maybe
    // to always render a search results page immediately, with a spinner
    // and then do the query with useEffect() from that page component?
    // That would mean a change to the router to allow routes that don't
    // have a fetch method. But it would give the search page better
    // control over how it handles its own errors.
    //
    // Doing that would also mean that the Route would have to handle
    // all of its own analytics... Router won't know how long fetching
    // takes and when the page is actually complete. So maybe this is
    // not a good idea. (Though some routes might want to be able to
    // specify that they always do a preliminary render before the fetch?)
    //
    fetch({ query }: SearchRouteParams): Promise<SearchResults> {
        let encoded = encodeURIComponent(query);
        let url = `/api/v1/search/${this.locale}?q=${encoded}`;
        return fetch(url)
            .then(response => response.json())
            .then(results => results && results.hits.hits.map(h => h._source));
    }

    getTitle({ query }: SearchRouteParams): string {
        return `Search results for: ${query} | MDN`;
    }
}

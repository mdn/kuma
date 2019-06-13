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

export type SearchResults = Array<{
    slug: string,
    title: string,
    summary: string,
    tags: Array<string>
}>;

const styles = {
    results: css({
        margin: '0 24px'
    }),
    container: css({
        display: 'flex',
        flexDirection: 'row',
        maxWidth: 1200,
        margin: '20px auto'
    }),
    result: css({
        flex: '2 1 500px'
    }),
    link: css({
        fontWeight: 'bold'
    }),
    summary: css({}),
    url: css({
        fontSize: 12
    }),
    tags: css({
        flex: '1 0 250px',
        paddingLeft: 30,
        alignSelf: 'center'
    }),
    tag: css({
        whiteSpace: 'nowrap',
        fontSize: 12,
        lineHeight: 1.2,
        backgroundColor: '#f5f9fa',
        border: 'solid 1px #dce3e5',
        borderRadius: 5,
        padding: '2px 4px',
        marginRight: 8
    })
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
            <div css={styles.results}>
                {data &&
                    data.map(hit => {
                        let path = `/${locale}/docs/${hit.slug}`;
                        let url =
                            window && window.origin
                                ? `${window.origin}${path}`
                                : path;
                        return (
                            <div css={styles.container} key={hit.slug}>
                                <div css={styles.result}>
                                    <div>
                                        <a css={styles.link} href={path}>
                                            {hit.title}
                                        </a>
                                    </div>
                                    <div css={styles.url}>{url}</div>
                                    <div css={styles.summary}>
                                        {hit.summary}
                                    </div>
                                </div>
                                <div css={styles.tags}>
                                    {hit.tags
                                        .filter(tag => !tag.startsWith('Needs'))
                                        .map(tag => (
                                            <>
                                                <span
                                                    css={styles.tag}
                                                    key={tag}
                                                >
                                                    {tag}
                                                </span>{' '}
                                            </>
                                        ))}
                                </div>
                            </div>
                        );
                    })}
            </div>
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

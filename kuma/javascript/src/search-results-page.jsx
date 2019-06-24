// @flow
import * as React from 'react';
import { css } from '@emotion/core';

import { gettext, interpolate } from './l10n.js';
import Header from './header/header.jsx';
import Route from './route.js';
import Titlebar from './titlebar.jsx';

type SearchRouteParams = {
    locale: string,
    query: string
};

export type SearchResults = {
    results: ?Array<{
        slug: string,
        title: string,
        summary: string,
        tags: Array<string>,
        score: number,
        excerpt: string
    }>,
    error: ?any
};

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
    excerpt: css({
        padding: 8,
        fontStyle: 'italic',
        fontSize: 12
    }),
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
    }),
    error: css({
        margin: 16,
        padding: 16,
        border: 'solid red 2px'
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
            <Header searchQuery={query} />
            <Titlebar title={`${gettext('Results')}: ${query}`} />
            <div css={styles.results}>
                {data &&
                    data.results &&
                    data.results.map(hit => {
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
                                    <div
                                        css={styles.excerpt}
                                        dangerouslySetInnerHTML={{
                                            __html: hit.excerpt
                                        }}
                                    />
                                </div>
                                <div css={styles.tags}>
                                    {hit.tags
                                        .filter(tag => !tag.startsWith('Needs'))
                                        .map(tag => (
                                            <React.Fragment key={tag}>
                                                <span css={styles.tag}>
                                                    {tag}
                                                </span>{' '}
                                            </React.Fragment>
                                        ))}
                                </div>
                            </div>
                        );
                    })}
                {data && data.error && (
                    <div css={styles.error}>
                        <h2>{data.error.toString()}</h2>
                    </div>
                )}
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

    fetch({ query }: SearchRouteParams): Promise<SearchResults> {
        let encoded = encodeURIComponent(query);
        let url = `/api/v1/search/${this.locale}?q=${encoded}`;
        return (
            fetch(url)
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error(
                            `${response.status} ${
                                response.statusText
                            } fetching ${url}`
                        );
                    }
                })
                .then(results => {
                    if (
                        !results ||
                        !results.hits ||
                        !Array.isArray(results.hits.hits)
                    ) {
                        throw new Error('Search API returned unexpected data');
                    }
                    return {
                        results: results.hits.hits.map(hit => {
                            let score = hit._score;
                            let excerpt =
                                hit.highlight &&
                                hit.highlight.content &&
                                hit.highlight.content[0];

                            return { ...hit._source, score, excerpt };
                        }),
                        error: null
                    };
                })
                // If anything goes wrong while we're fetching, just
                // return the error we got and let the search results
                // page display it.  If we don't do this and let the
                // error propagate to the router the router will fall
                // back on a full page reload. But for this route that
                // will just cause the error again and will result in
                // an infinite reload loop.
                .catch(error => ({ error, results: null }))
        );
    }

    getTitle({ query }: SearchRouteParams): string {
        return `${interpolate(
            gettext('Search results for "%(query)s"'),
            {
                query
            },
            true
        )} | MDN`;
    }
}

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
        score: number,
        excerpts: Array<string>
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
    summary: css({
        marginBottom: 8
    }),
    excerpt: css({
        padding: '2px 24px',
        fontStyle: 'italic',
        fontSize: 12,
        // Sometimes elasticsearch gives us excerpts with no spaces
        // and we have to force the words to wrap.
        overflowWrap: 'anywhere',

        '& mark': {
            fontWeight: 'bold',
            backgroundColor: 'inherit'
        },
        ':before': {
            content: '"..."'
        },
        ':after': {
            content: '"..."'
        }
    }),
    url: css({
        fontSize: 12
    }),
    noresults: css({
        fontWeight: 'bold',
        maxWidth: 1200,
        margin: '20px auto'
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
                                    <div css={styles.url}>
                                        <a href={path}>{url}</a>
                                    </div>
                                    <div css={styles.summary}>
                                        {hit.summary}
                                    </div>
                                    {hit.excerpts.map((excerpt, i) => (
                                        <div
                                            css={styles.excerpt}
                                            key={i}
                                            dangerouslySetInnerHTML={{
                                                __html: excerpt
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                {data && data.results && data.results.length === 0 && (
                    <div css={styles.noresults}>
                        {gettext('No matching documents found.')}
                    </div>
                )}
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
                            let excerpts =
                                (hit.highlight && hit.highlight.content) || [];

                            // Sometimes ElasticSearch returns excerpts that
                            // are thousands of bytes long without any spaces
                            // and we don't want to display those
                            if (excerpts) {
                                excerpts = excerpts.filter(e => e.length < 256);
                            }

                            // And we only want to display the top 3 excerpts
                            if (excerpts && excerpts.length > 3) {
                                excerpts = excerpts.slice(0, 3);
                            }
                            return { ...hit._source, score, excerpts };
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

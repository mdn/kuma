// @flow
import * as React from 'react';

import { gettext, interpolate, ngettext } from './l10n.js';
import Header from './header/header.jsx';
import Route from './route.js';
import Titlebar from './titlebar.jsx';

type SearchRouteParams = {
    locale: string,
    query: string,
    page: ?number
};

type SearchResults = {
    count: number,
    documents: ?Array<{
        slug: string,
        title: string,
        locale: string,
        excerpt: string
    }>,
    start: number,
    end: number,
    filters: ?any, // TODO specify this maybe
    locale: string,
    next: ?string,
    page: number,
    pages: number,
    previous: ?string,
    query: string
};
export type SearchResultsResponse = {
    results: ?SearchResults,
    error: ?any
};

type Props = {
    locale: string,
    query: string,
    data: ?SearchResultsResponse
};

function makePaginationPageURL(uri) {
    return uri ? `?${uri.split('?')[1]}` : '';
}

function ResultsMeta({
    locale,
    results: { count, previous, next, query, start, end }
}: {
    locale: string,
    results: SearchResults
}) {
    let resultsText;
    if (count > 0) {
        if (previous || next) {
            resultsText = interpolate(
                gettext('Showing results %(start)s to %(end)s.'),
                { start, end }
            );
        } else {
            resultsText = gettext('Showing all ');
        }
    }
    return (
        <div className="result-container">
            <p className="result-meta">
                {interpolate(
                    ngettext(
                        '%(count)s document found for "%(query)s" in %(locale)s.',
                        '%(count)s documents found for "%(query)s" in %(locale)s.',
                        count
                    ),
                    {
                        count: count.toLocaleString(),
                        // XXX this 'locale' is something like 'en-US'
                        // need to turn that into "English (US)".
                        locale,
                        query
                    }
                )}{' '}
                {resultsText}
            </p>
        </div>
    );
}

function Results({
    locale,
    results
}: {
    locale: string,
    results: SearchResults
}) {
    return (results.documents || []).map(result => {
        const path = `/${locale}/docs/${result.slug}`;
        const url = window && window.origin ? `${window.origin}${path}` : path;
        return (
            <div className="result-container" key={result.slug}>
                <div className="result">
                    <div>
                        <a className="result-title" href={path}>
                            {result.title}
                        </a>
                    </div>
                    <div
                        className="result-excerpt"
                        dangerouslySetInnerHTML={{
                            __html: result.excerpt
                        }}
                    />
                    <div className="result-url">
                        <a href={path}>{url}</a>
                    </div>
                </div>
            </div>
        );
    });
}

function Pager({ previous, next }: { previous: ?string, next: ?string }) {
    return (
        <div className="result-container results-more">
            <div>
                {previous && (
                    <a
                        className="button"
                        href={makePaginationPageURL(previous)}
                        id="search-result-previous"
                    >
                        {gettext('Previous')}
                    </a>
                )}{' '}
                {next && (
                    <a
                        className="button"
                        href={makePaginationPageURL(next)}
                        id="search-result-next"
                    >
                        {gettext('Next')}
                    </a>
                )}
            </div>
        </div>
    );
}

export default function SearchResultsPage({ locale, query, data }: Props) {
    const results = data ? data.results : null;
    return (
        <>
            <Header searchQuery={query} />
            {query && <Titlebar title={`${gettext('Results')}: ${query}`} />}

            <div className="search-results">
                {data && (
                    <>
                        {results && (
                            <>
                                <ResultsMeta {...{ results, locale }} />

                                <Results {...{ results, locale }} />

                                {(results.previous || results.next) && (
                                    <Pager
                                        previous={results.previous}
                                        next={results.next}
                                    />
                                )}

                                {results.count === 0 && (
                                    <div className="result-container">
                                        <div className="no-results">
                                            {gettext(
                                                'No matching documents found.'
                                            )}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}

                        {data.error && (
                            <div className="result-container">
                                <div className="error">
                                    <h2>{data.error.toString()}</h2>
                                </div>
                            </div>
                        )}
                    </>
                )}

                {!query && (
                    <div className="result-container">
                        <p>
                            <i>
                                {gettext('Nothing found if nothing searched.')}
                            </i>
                        </p>
                    </div>
                )}
            </div>
        </>
    );
}

// This Route subclass tells the Router component how to convert
// search URLs into SearchResultPage components. See route.js and router.jsx.
export class SearchRoute extends Route<
    SearchRouteParams,
    SearchResultsResponse
> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return SearchResultsPage;
    }

    match(url: string): ?SearchRouteParams {
        // In order to use new URL() with relative URLs, we need an absolute
        // base URL.
        let parsed = new URL(url, 'http://ssr.hack');

        let path = parsed.pathname;
        let query = parsed.searchParams.get('q') || '';
        let page = parseInt(parsed.searchParams.get('page') || '1');
        if (isNaN(page) || page <= 0) {
            page = null;
        }

        if (path !== `/${this.locale}/search`) {
            return null;
        }

        return { locale: this.locale, query, page };
    }

    fetch({ query, page }: SearchRouteParams): Promise<SearchResultsResponse> {
        if (!query) {
            // Every route component *has* to return a promise from the
            // fetch() method because it's called unconditionally.
            // But if there is no query, there's no need to do an XHR
            // request.
            // By returning a promise that always resolves to nothing we
            // can deal with that fact inside the SearchResultsPage
            // component.
            // By the way, the only way you can get to the search page
            // with a falsy query is if you manually remove the `?q=...`
            // from the current URL.
            // This is all about avoiding returning a completely blank
            // page.
            return Promise.resolve({
                results: null,
                error: null
            });
        }
        let encoded = encodeURIComponent(query);
        let url = `/api/v1/search/${this.locale}?q=${encoded}`;
        url += `&locale=${this.locale}`;
        if (page && page > 1) {
            url += `&page=${page}`;
        }

        return (
            fetch(url)
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error(
                            `${response.status} ${response.statusText} fetching ${url}`
                        );
                    }
                })
                .then(results => {
                    if (
                        !results ||
                        !results.documents ||
                        !Array.isArray(results.documents)
                    ) {
                        throw new Error('Search API returned unexpected data');
                    }

                    return {
                        results,
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
        return `${interpolate(gettext('Search results for "%(query)s"'), {
            query
        })} | MDN`;
    }
}

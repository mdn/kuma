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

export default function SearchResultsPage({ locale, query, data }: Props) {
    // Because it's clunky to do conditionals in JSX, let's create all the
    // React nodes here first.
    let resultsMetaNode = null;
    let resultsNode = null;
    let noResultsNode = null;
    let pagerNode = null;
    let errorNode = null;
    let noQuery = null;

    if (!query) {
        noQuery = (
            <div className="result-container">
                <p>
                    <i>{gettext('Nothing found if nothing searched.')}</i>
                </p>
            </div>
        );
    }

    if (data) {
        const { results } = data;

        if (results) {
            if (results.previous || results.next) {
                pagerNode = (
                    <div className="result-container results-more">
                        <div>
                            {results.previous && (
                                <a
                                    className="button"
                                    href={makePaginationPageURL(
                                        results.previous
                                    )}
                                    id="search-result-previous"
                                >
                                    {gettext('Previous')}
                                </a>
                            )}{' '}
                            {results.next && (
                                <a
                                    className="button"
                                    href={makePaginationPageURL(results.next)}
                                    id="search-result-next"
                                >
                                    {gettext('Next')}
                                </a>
                            )}
                        </div>
                    </div>
                );
            }

            resultsNode = (results.documents || []).map(result => {
                let path = `/${locale}/docs/${result.slug}`;
                let url =
                    window && window.origin ? `${window.origin}${path}` : path;
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

            resultsMetaNode = (
                <div className="result-container">
                    <p className="result-meta">
                        {interpolate(
                            ngettext(
                                '%(count)s document found for "%(query)s" in %(locale)s.',
                                '%(count)s documents found for "%(query)s" in %(locale)s.',
                                results.count
                            ),
                            {
                                count: results.count.toLocaleString(),
                                // XXX this 'locale' is something like 'en-US'
                                // need to turn that into "English (US)".
                                locale: locale,
                                query: results.query
                            },
                            true
                        )}{' '}
                        {!!results.count &&
                            !results.previous &&
                            !results.next &&
                            gettext('Showing all results.')}
                        {!!results.count &&
                            (results.previous || results.next) &&
                            interpolate(
                                gettext(
                                    'Showing results %(start)s to %(end)s.'
                                ),
                                {
                                    start: results.start,
                                    end: results.end
                                },
                                true
                            )}
                    </p>
                </div>
            );

            if (results.count === 0) {
                noResultsNode = (
                    <div className="result-container">
                        <div className="no-results">
                            {gettext('No matching documents found.')}
                        </div>
                    </div>
                );
            }
        }

        if (data.error) {
            errorNode = (
                <div className="result-container">
                    <div className="error">
                        <h2>{data.error.toString()}</h2>
                    </div>
                </div>
            );
        }
    }

    return (
        <>
            <Header searchQuery={query} />
            {query && <Titlebar title={`${gettext('Results')}: ${query}`} />}

            <div className="search-results">
                {resultsMetaNode}

                {resultsNode}

                {pagerNode}

                {noResultsNode}

                {errorNode}

                {noQuery}
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
        let parsed = new URL(url, BASEURL);

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
        return `${interpolate(
            gettext('Search results for "%(query)s"'),
            {
                query
            },
            true
        )} | MDN`;
    }
}

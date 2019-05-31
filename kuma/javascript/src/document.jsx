// @flow
import * as React from 'react';
import { css } from '@emotion/core';

import Article from './article.jsx';
import { gettext } from './l10n.js';
import LanguageMenu from './header/language-menu.jsx';
import Header from './header/header.jsx';
import TaskCompletionSurvey from './task-completion-survey.jsx';
import Titlebar from './titlebar.jsx';

import type Route from './router.jsx';

export type DocumentData = {
    locale: string,
    slug: string,
    enSlug: string, // For non-english documents, the original english slug
    id: number,
    title: string,
    summary: string,
    language: string,
    hrefLang: string,
    absoluteURL: string,
    editURL: string,
    bodyHTML: string,
    quickLinksHTML: string,
    tocHTML: string,
    parents: Array<{ url: string, title: string }>,
    translations: Array<{
        locale: string,
        language: string,
        hrefLang: string,
        localizedLanguage: string,
        url: string,
        title: string
    }>,
    contributors: Array<string>,
    lastModified: string, // An ISO date
    lastModifiedBy: string
};

export type DocumentProps = {
    document: DocumentData
};

// A media query that identifies screens narrower than a tablet
const NARROW = '@media (max-width: 749px)';

const styles = {
    // Breadcrumbs styles
    breadcrumbsContainer: css({
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%',
        minHeight: 40,
        padding: '4px 16px 4px 24px',
        borderBottom: 'solid 1px #dce3e5',
        backgroundColor: '#fff'
    }),
    breadcrumbsRow: css({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        width: '100%',
        maxWidth: 1360
    }),
    breadcrumbs: css({
        flex: '1 1'
    }),
    crumb: css({
        display: 'inline',
        fontSize: 14,
        hyphens: 'auto',
        '&a': {
            color: '#3d7e9a'
        }
    }),
    chevron: css({
        fontFamily: 'zillaslab,serif',
        fontWeight: 'bold',
        fontSize: 18,
        margin: '0 8px'
    }),

    // Content styles: the sidebar and main article content
    contentLayout: css({
        display: 'grid',
        boxSizing: 'border-box',
        maxWidth: 1400,
        margin: '0 auto',
        gridTemplateColumns: '25% 75%',
        gridTemplateAreas: '"side main"',
        [NARROW]: {
            // If we're narrower than a tablet, put the sidebar at the
            // bottom and drop the toc line.
            gridTemplateColumns: '1fr',
            gridTemplateAreas: '"main" "side"'
        }
    }),
    sidebar: css({
        gridArea: 'side',
        boxSizing: 'border-box',
        width: '100%',
        overflowX: 'scroll',
        // Less padding on the right because the article area
        // has padding on the left, too.
        padding: '30px 12px 30px 24px',
        [NARROW]: {
            // Except that on small screens the sidebar is at the bottom and
            // so we need the same padding (but less of it) on both sides.
            padding: '15px 12px'
        }
    }),
    tocHeader: css({
        height: 4,
        margin: '0 12px 0 -1px',
        backgroundImage: 'linear-gradient(-272deg, #206584, #83d0f2)'
    }),
    toc: css({
        backgroundColor: '#fcfcfc',
        border: 'solid 1px #dce3e5',
        padding: '8px 8px 0px 13px',
        margin: '0 12px 20px -1px',
        '& ul': {
            listStyle: 'none',
            paddingLeft: 12
        },
        '& li': {
            fontSize: 14,
            lineHeight: '20px',
            margin: '10px 0'
        }
    }),
    sidebarHeading: css({
        fontFamily:
            'x-locale-heading-primary, zillaslab, "Palatino", "Palatino Linotype", x-locale-heading-secondary, serif',
        fontSize: 20,
        height: 24,
        marginBottom: 16
    })
};

function Sidebar({ document }: DocumentProps) {
    // TODO(djf): We may want to omit the "On this Page" section from
    // the sidebar for pages with slugs like /Web/*/*/*: those are
    // mostly HTML and CSS reference pages with repetitive TOCs. The
    // TOC would afford quick access to the BCD table, but might not
    // be useful for much else. For Learn/ slugs, however, the TOC is
    // likely to be much more informative. I think a decision is still
    // needed here. For now, we show the TOC on all pages that have one.
    let showTOC = !!document.tocHTML;

    return (
        <div css={styles.sidebar}>
            {showTOC && (
                <>
                    <div css={styles.tocHeader} />
                    <div css={styles.toc}>
                        <div css={styles.sidebarHeading}>
                            {gettext('On this Page')}
                        </div>
                        <ul
                            dangerouslySetInnerHTML={{
                                __html: document.tocHTML
                            }}
                        />
                    </div>
                </>
            )}
            <div className="quick-links">
                <div css={styles.sidebarHeading} className="quick-links-head">
                    {gettext('Related Topics')}
                </div>
                <div
                    dangerouslySetInnerHTML={{
                        __html: document.quickLinksHTML
                    }}
                />
            </div>
        </div>
    );
}

function Chevron() {
    return <span css={styles.chevron}>›</span>;
}

function Breadcrumbs({ document }: DocumentProps) {
    // The <span> elements below aren't needed except that the stylesheets
    // are set up to expect them.
    return (
        <div css={styles.breadcrumbsContainer}>
            <div css={styles.breadcrumbsRow}>
                <nav css={styles.breadcrumbs} role="navigation">
                    <ol>
                        {document.parents.map(p => (
                            <li css={styles.crumb} key={p.url}>
                                <a href={p.url}>
                                    <span>{p.title}</span>
                                </a>
                                <Chevron />
                            </li>
                        ))}
                        <li css={styles.crumb}>
                            <span>{document.title}</span>
                        </li>
                    </ol>
                </nav>
                <LanguageMenu document={document} />
            </div>
        </div>
    );
}

function Content({ document }: DocumentProps) {
    return (
        <div css={styles.contentLayout}>
            <Article document={document} />
            <Sidebar document={document} />
        </div>
    );
}

function DocumentPage({ document }: DocumentProps) {
    return (
        <>
            <Header document={document} />
            <TaskCompletionSurvey document={document} />
            <Titlebar title={document.title} document={document} />
            <Breadcrumbs document={document} />
            <Content document={document} />
        </>
    );
}

type Props = { data: ?DocumentData };

export default function Document({ data }: Props) {
    if (data) {
        return <DocumentPage document={data} />;
    } else {
        return null;
    }
}

// Like fetch(), but if the first URL doesn't work, try the second instead.
function fetchWithFallback(url1: string, url2: string) {
    const fetchConfig = { redirect: 'follow' };
    return fetch(url1, fetchConfig).then(response => {
        if (response.ok || !url2 || url2 === url1) {
            return response;
        } else {
            return fetch(url2, fetchConfig);
        }
    });
}

// In order to use new URL() with relative URLs, we need an absolute base
// URL. If we're running in the browser we can use our current page URL.
// But if we're doing SSR, we just have to make something up.
const BASEURL =
    typeof window !== 'undefined' && window.location
        ? window.location.origin
        : 'http://ssr.hack';

type DocumentRouteData = {
    locale: string,
    slug: string
};

// This Route object tells the Router component how to convert
// /docs/ URLs into Document components. See router.jsx for details.
export const DocumentRoute: Route = {
    component: Document,

    match(url: string): ?DocumentRouteData {
        let path = new URL(url, BASEURL).pathname;
        let m = path.match(/^\/([^/]+)\/docs\/(.*)$/);
        if (m && m[1] && m[2]) {
            return {
                locale: m[1],
                slug: m[2]
            };
        } else {
            // Returning null means we can't handle the url
            return null;
        }
    },

    fetch({ locale, slug }: DocumentRouteData): Promise<DocumentData> {
        // The fallback is for the case when we request a non-English
        // document that doesn't exist. In that case, before we abandon
        // client-side navigation, we'll try falling-back to the English
        // document.
        return fetchWithFallback(
            `/api/v1/doc/${locale}/${slug}`,
            `/api/v1/doc/en-US/${slug}`
        )
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    // If we didn't get a good response, throw an error
                    // that we'll handle in the catch() function below.
                    throw new Error(
                        `${response.status}:${response.statusText}`
                    );
                }
            })
            .then(json => {
                if (json && json.redirectURL) {
                    // We've got a redirect to a document that can't be
                    // handled via the /api/v1/doc/ API, so we just do a
                    // full page load of that document.
                    window.location = json.redirectURL;
                    // Reloading the page means that this return doesn't
                    // really matter, but flow gets confused if we don't
                    // return some kind of "document data" here
                    return {};
                } else if (json && json.documentData) {
                    let documentData = json.documentData;

                    // If the slug of the received document is different
                    // than the slug we requested, then we were redirected
                    // and we need to fix up the URL in the location bar
                    if (documentData.slug !== slug) {
                        let url = documentData.absoluteURL;
                        history.replaceState(url, '', url);
                    }

                    return documentData;
                } else {
                    throw new Error('Invalid response from document API');
                }
            });
    },

    title(matchedData, fetchedData) {
        return fetchedData.title;
    },

    gaHook(ga, matchedData, fetchedData) {
        // If the document data includes enSlug, or if the
        // document is in english, then pass the slug to
        // google analytics as dimension 17.
        if (fetchedData.enSlug) {
            ga('set', 'dimension17', fetchedData.enSlug);
        } else if (fetchedData.locale === 'en-US') {
            ga('set', 'dimension17', fetchedData.slug);
        }
    }
};

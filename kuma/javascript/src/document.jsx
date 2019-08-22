// @flow
import * as React from 'react';
import { css } from '@emotion/core';

import A11yNav from './a11y/a11y-nav.jsx';
import Article from './article.jsx';
import Banners from './banners.jsx';
import Breadcrumbs from './breadcrumbs.jsx';
import { gettext } from './l10n.js';
import LanguageMenu from './header/language-menu.jsx';
import Header from './header/header.jsx';
import Route from './route.js';
import TaskCompletionSurvey from './task-completion-survey.jsx';
import Titlebar from './titlebar.jsx';
import TOC from './toc.jsx';

import type { GAFunction } from './ga-provider.jsx';

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
    translateURL: string,
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

// Content styles: the sidebar and main article content
const styles = {
    contentLayout: css({
        display: 'grid',
        boxSizing: 'border-box',
        maxWidth: 1400,
        margin: '0 auto',
        gridTemplateColumns: '25% 75%',
        gridTemplateRows: 'max-content 1fr',
        gridTemplateAreas: '"document-toc-container main" "side main"',
        [NARROW]: {
            // If we're narrower than a tablet, put the sidebar at the
            // bottom and drop the toc line.
            gridTemplateColumns: '100%',
            gridTemplateAreas: '"main" "document-toc-container" "side"'
        }
    }),
    sidebar: css({
        gridArea: 'side',
        boxSizing: 'border-box',
        width: '100%',
        // Less padding on the right because the article area
        // has padding on the left, too.
        padding: '30px 12px 30px 24px',
        [NARROW]: {
            // Except that on small screens the sidebar is at the bottom and
            // so we need the same padding (but less of it) on both sides.
            padding: '15px 12px'
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

export function Sidebar({ document }: DocumentProps) {
    return (
        <div css={styles.sidebar}>
            {document.quickLinksHTML && (
                <div className="quick-links">
                    <div
                        css={styles.sidebarHeading}
                        className="quick-links-head"
                    >
                        {gettext('Related Topics')}
                    </div>
                    <div
                        dangerouslySetInnerHTML={{
                            __html: document.quickLinksHTML
                        }}
                    />
                </div>
            )}
        </div>
    );
}

function Content({ document }: DocumentProps) {
    // The wiki-left-present class below is needed for correct BCD layout
    // See kuma/static/styles/components/compat-tables/bc-table.scss
    return (
        /* adding aria-live here to mark this as a live region to
          ensure a screen reader will read the new content after navigation */
        <div
            css={styles.contentLayout}
            className="wiki-left-present"
            // See https://bugzilla.mozilla.org/show_bug.cgi?id=1570043
            // aria-live="assertive"
        >
            {!!document.tocHTML && <TOC html={document.tocHTML} />}
            <Article document={document} />
            <Sidebar document={document} />
        </div>
    );
}

function DocumentPage({ document }: DocumentProps) {
    return (
        <>
            <A11yNav />
            <Header document={document} />
            <main role="main">
                <Titlebar title={document.title} document={document} />
                <div className="full-width-row-container">
                    <div className="max-content-width-container">
                        <Breadcrumbs document={document} />
                        <LanguageMenu document={document} />
                    </div>
                </div>
                <Content document={document} />
            </main>
            <TaskCompletionSurvey document={document} />
            <Banners />
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
    return fetch(url1).then(response => {
        if (response.ok || !url2 || url2 === url1) {
            return response;
        } else {
            return fetch(url2);
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

type DocumentRouteParams = {
    locale: string,
    slug: string
};

// This Route subclass tells the Router component how to convert
// /docs/ URLs into Document components. See router.jsx for details.
export class DocumentRoute extends Route<DocumentRouteParams, DocumentData> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return Document;
    }

    match(url: string): ?DocumentRouteParams {
        let path = new URL(url, BASEURL).pathname;
        // Require locales to match because we only have one set
        // of translation strings loaded currently. If the user switches
        // locales we want to do a full page reload so we get new strings.
        let expectedPrefix = `/${this.locale}/docs/`;
        if (!path.startsWith(expectedPrefix)) {
            return null;
        }

        return {
            locale: this.locale,
            slug: path.substring(expectedPrefix.length)
        };
    }

    fetch({ locale, slug }: DocumentRouteParams): Promise<DocumentData> {
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
                    // for the Router component to handle
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
    }

    getTitle(params: DocumentRouteParams, data: DocumentData) {
        return data.title;
    }

    analyticsHook(
        ga: GAFunction,
        params: DocumentRouteParams,
        data: DocumentData
    ) {
        // If the document data includes enSlug, or if the
        // document is in english, then pass the slug to
        // google analytics as dimension 17.
        if (data.enSlug) {
            ga('set', 'dimension17', data.enSlug);
        } else if (data.locale === 'en-US') {
            ga('set', 'dimension17', data.slug);
        }
    }
}

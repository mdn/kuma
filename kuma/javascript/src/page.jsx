// @flow
import * as React from 'react';
import { useContext, useEffect } from 'react';
import { css } from '@emotion/core';

import Article from './article.jsx';
import DocumentProvider from './document-provider.jsx';
import GAProvider from './ga-provider.jsx';
import { gettext } from './l10n.js';
import LanguageMenu from './header/language-menu.jsx';
import { Row } from './layout.jsx';
import Header from './header/header.jsx';
import TaskCompletionSurvey from './task-completion-survey.jsx';
import { navigateRenderComplete } from './perf.js';

import type { DocumentData } from './document-provider.jsx';
type DocumentProps = {
    document: DocumentData
};

// A media query that identifies screens narrower than a tablet
const NARROW = '@media (max-width: 749px)';

const styles = {
    pageLayout: css({
        display: 'grid',
        boxSizing: 'border-box',
        gridTemplateColumns: '1fr 3fr',
        gridTemplateAreas: '"title title" "crumbs crumbs"  "side main"',
        [NARROW]: {
            // If we're narrower than a tablet, put the sidebar at the
            // bottom and drop the toc line.
            gridTemplateColumns: '1fr',
            gridTemplateAreas: '"title" "crumbs" "main" "side"'
        }
    }),
    titlebar: css({
        gridArea: 'title',
        boxSizing: 'border-box',
        width: '100%',
        minHeight: 106,
        padding: '12px 24px',
        overflowX: 'scroll',
        backgroundColor: '#f5f9fa',
        borderBottom: 'solid 1px #dce3e5',
        borderTop: 'solid 1px #dce3e5',
        [NARROW]: {
            // Reduce titlebar size on narrow screens
            minHeight: 60,
            padding: '8px 16px'
        }
    }),
    title: css({
        fontFamily:
            'x-locale-heading-primary, zillaslab, "Palatino", "Palatino Linotype", x-locale-heading-secondary, serif',
        fontSize: 45,
        fontWeight: 'bold',
        [NARROW]: {
            // Reduce the H1 size on narrow screens
            fontSize: 28
        }
    }),
    breadcrumbsRow: css({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gridArea: 'crumbs',
        boxSizing: 'border-box',
        width: '100%',
        minHeight: 40,
        padding: '4px 16px 4px 24px',
        borderBottom: 'solid 1px #dce3e5',
        backgroundColor: '#fff'
    }),
    breadcrumbs: css({
        display: 'flex',
        flexDirection: 'row',
        flex: '1 1'
    }),
    crumb: css({
        display: 'inline',
        fontSize: 14,
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
    related: css({
        fontSize: 20
    })
};

function Titlebar({ document }: DocumentProps) {
    return (
        <Row css={styles.titlebar}>
            <h1 css={styles.title}>{document.title}</h1>
        </Row>
    );
}

function Sidebar({ document }: DocumentProps) {
    return (
        <div className="quick-links" css={styles.sidebar}>
            <div css={styles.related} className="quick-links-head">
                {gettext('Related Topics')}
            </div>
            <div
                dangerouslySetInnerHTML={{
                    __html: document.quickLinksHTML
                }}
            />
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
            <LanguageMenu />
        </div>
    );
}

function Document() {
    const document = useContext(DocumentProvider.context);
    const ga = useContext(GAProvider.context);

    /*
     * Register an effect that runs every time we see a new document URL.
     * The effect sends a Google Analytics timing event to record how long
     * it took from the start of the navigation until the new document is
     * rendered.
     *
     * Effects don't run during server-side-rendering, but that is fine
     * because we only want to send the GA event for client-side navigation.
     * Calling navigateRenderComplete() will have no effect if
     * navigateStart() was not previously called.
     */
    useEffect(() => {
        navigateRenderComplete(ga);
    }, [document && document.absoluteURL]);

    return (
        document && (
            <div css={styles.pageLayout}>
                <Titlebar document={document} />
                <Breadcrumbs document={document} />
                <Article document={document} />
                <Sidebar document={document} />
            </div>
        )
    );
}

export default function Page() {
    return (
        <>
            <Header />
            <TaskCompletionSurvey />
            <Document />
        </>
    );
}

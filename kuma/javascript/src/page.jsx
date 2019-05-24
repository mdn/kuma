// @flow
import * as React from 'react';
import { useContext, useEffect } from 'react';
import { css } from '@emotion/core';

import ClockIcon from './icons/clock.svg';
import ContributorsIcon from './icons/contributors.svg';
import DocumentProvider from './document-provider.jsx';
import GAProvider from './ga-provider.jsx';
import { getLocale, gettext } from './l10n.js';
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
        gridTemplateAreas: '"title title"  "toc toc"  "side main"',
        [NARROW]: {
            // If we're narrower than a tablet, put the sidebar at the
            // bottom and drop the toc line.
            gridTemplateColumns: '1fr',
            gridTemplateAreas: '"title" "main" "side"'
        }
    }),
    titlebar: css({
        gridArea: 'title',
        boxSizing: 'border-box',
        width: '100%',
        height: 106,
        paddingLeft: 24,
        overflowX: 'scroll',
        backgroundColor: '#f5f9fa',
        border: 'solid 1px #dce3e5',
        [NARROW]: {
            // Reduce titlebar size on narrow screens
            height: 60,
            paddingLeft: 16
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
    toc: css({
        gridArea: 'toc',
        boxSizing: 'border-box',
        width: '100%',
        overflowX: 'scroll',
        color: '#fff',
        backgroundColor: '#222',
        padding: '8px 8px 8px 24px',
        [NARROW]: {
            // We don't display the TOC bar on small screens.
            // Leaving it out of the grid is not enough, though:
            // we also have to explicitly hide it.
            display: 'none'
        },

        '& li': {
            display: 'inline-block'
        },
        '& a': {
            color: '#83d0f2',
            paddingRight: 30,
            whiteSpace: 'nowrap',
            textDecoration: 'none',
            fontSize: '1rem'
        },

        '& code': {
            backgroundColor: 'inherit',
            color: 'inherit',
            fontFamily: 'inherit',
            fontSize: 'inherit',
            padding: 0
        },

        // Don't display any nested lists in the TOC
        // This may not be needed anymore, but there are still documents
        // on staging that have nested lists in the TOC. Re-rendering those
        // docs seems to make the nested lists go away, but this is here
        // just in case
        '& li ol, li ul': {
            display: 'none'
        }
    }),
    article: css({
        gridArea: 'main',
        boxSizing: 'border-box',
        width: '100%',
        overflowX: 'scroll',
        // Less padding on the left because the sidebar also has
        // padding on the right
        padding: '30px 24px 30px 12px',
        [NARROW]: {
            // Except on small screens the sidebar is below, so we
            // need the same (but overall smaller) padding on both sides.
            padding: '15px 12px'
        },
        '& p': {
            maxWidth: '42rem'
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
    breadcrumbs: css({}),
    quicklinks: css({}),

    metadata: css({
        marginTop: 32,
        fontSize: '0.88889rem',
        color: '#696969',
        '& div': {
            margin: '4px 0'
        }
    }),
    contributorsIcon: css({
        width: 14,
        height: 14,
        marginRight: 5,
        verticalAlign: 'middle',
        fill: '#696969'
    }),
    clockIcon: css({
        width: 16,
        height: 16,
        marginRight: 5,
        verticalAlign: 'middle',
        fill: '#696969'
    })
};

function Titlebar({ document }: DocumentProps) {
    return (
        <Row css={styles.titlebar}>
            <h1 css={styles.title}>{document.title}</h1>
        </Row>
    );
}

function TOC({ document }: DocumentProps) {
    return (
        <Row
            css={styles.toc}
            dangerouslySetInnerHTML={{
                __html: `<ol>${document.tocHTML}</ol>`
            }}
        />
    );
}

function Sidebar({ document }: DocumentProps) {
    return (
        <div css={styles.sidebar}>
            <Breadcrumbs document={document} />
            <Quicklinks document={document} />
        </div>
    );
}

function Breadcrumbs({ document }: DocumentProps) {
    // The <span> elements below aren't needed except that the stylesheets
    // are set up to expect them.
    return (
        <nav className="crumbs" role="navigation">
            <ol>
                {document.parents.map(p => (
                    <li className="crumb" key={p.url}>
                        <a href={p.url}>
                            <span>{p.title}</span>
                        </a>
                    </li>
                ))}
                <li className="crumb">
                    <span>{document.title}</span>
                </li>
            </ol>
        </nav>
    );
}

function Quicklinks({ document }: DocumentProps) {
    return (
        <div className="quick-links" css={styles.quicklinks}>
            <div className="quick-links-head">{gettext('Related Topics')}</div>
            <div
                dangerouslySetInnerHTML={{
                    __html: document.quickLinksHTML
                }}
            />
        </div>
    );
}

function Article({ document }: DocumentProps) {
    return (
        /*
         * The "text-content" class and "wikiArticle" id are required
         * because our stylesheets expect them and formatting isn't quite
         * right without them.
         */
        <div className="text-content" css={styles.article}>
            <article
                id="wikiArticle"
                dangerouslySetInnerHTML={{ __html: document.bodyHTML }}
            />
            <ArticleMetadata document={document} />
        </div>
    );
}

function ArticleMetadata({ document }: DocumentProps) {
    const locale = getLocale();
    return (
        <div css={styles.metadata}>
            <div>
                <ContributorsIcon css={styles.contributorsIcon} />{' '}
                <strong>{gettext('Contributors to this page:')}</strong>{' '}
                {document.contributors.map((c, i) => (
                    <span key={c}>
                        {i > 0 && ', '}
                        <a href={`/${locale}/profiles/${c}`} rel="nofollow">
                            {c}
                        </a>
                    </span>
                ))}
            </div>
            <div>
                <ClockIcon css={styles.clockIcon} />{' '}
                <strong>{gettext('Last updated by:')}</strong>{' '}
                {document.lastModifiedBy}{' '}
                <time dateTime={document.lastModified}>
                    {new Date(document.lastModified)
                        .toISOString()
                        .slice(0, -5)
                        .replace('T', ' ')}
                </time>
            </div>
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
                <TOC document={document} />
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

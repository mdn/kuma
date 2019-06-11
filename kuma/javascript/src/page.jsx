// @flow
import * as React from 'react';
import { useContext, useEffect } from 'react';
import { css } from '@emotion/core';

import Article from './article.jsx';
import DocumentProvider from './document-provider.jsx';
import EditIcon from './icons/pencil.svg';
import GAProvider from './ga-provider.jsx';
import { gettext } from './l10n.js';
import HistoryIcon from './icons/clock.svg';
import LanguageMenu from './header/language-menu.jsx';
import Header from './header/header.jsx';
import TaskCompletionSurvey from './task-completion-survey.jsx';
import { navigateRenderComplete } from './perf.js';
import UserProvider from './user-provider.jsx';

import type { DocumentData } from './document-provider.jsx';
type DocumentProps = {
    document: DocumentData
};

// A media query that identifies screens narrower than a tablet
const NARROW = '@media (max-width: 749px)';

const styles = {
    // Titlebar styles
    titlebarContainer: css({
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
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
    titlebar: css({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        width: '100%',
        maxWidth: 1352
    }),
    title: css({
        flex: '1 1',
        fontFamily:
            'x-locale-heading-primary, zillaslab, "Palatino", "Palatino Linotype", x-locale-heading-secondary, serif',
        fontSize: 45,
        fontWeight: 'bold',
        hyphens: 'auto',
        [NARROW]: {
            // Reduce the H1 size on narrow screens
            fontSize: 28
        }
    }),

    editAndHistoryButtons: css({
        display: 'flex',
        flexDirection: 'row',
        flex: '0 0'
    }),
    editButton: css({
        height: 32,
        border: 'solid 2px #3d7e9a',
        color: '#3d7e9a', // for the text
        fill: '#3d7e9a', // for the icon
        backgroundColor: '#fff',
        whiteSpace: 'nowrap',
        fontSize: 15,
        fontWeight: 'bold',
        padding: '0 18px'
    }),
    historyButton: css({
        width: 32,
        height: 32,
        border: 'solid 2px #333',
        backgroundColor: '#fff',
        padding: 5,
        marginLeft: 8
    }),

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

function EditAndHistoryButtons({ document }: DocumentProps) {
    let editURL = document.editURL;
    return (
        <div css={styles.editAndHistoryButtons}>
            <button
                css={styles.editButton}
                onClick={() => {
                    window.location = editURL;
                }}
            >
                <EditIcon width={13} height={13} /> {gettext('Edit')}
            </button>
            <button
                css={styles.historyButton}
                aria-label={gettext('History')}
                onClick={() => {
                    window.location = editURL.replace('$edit', '$history');
                }}
            >
                <HistoryIcon width={18} height={18} />
            </button>
        </div>
    );
}

export function Titlebar({ document }: DocumentProps) {
    const userData = useContext(UserProvider.context);

    // If we have user data, and the user is logged in, and they
    // are a contributor (or, if we don't know whether they are
    // a contributor because the backend does not support that yet)
    // then we want to show Edit and History buttons on the
    // right side of the titlebar.
    let showEditAndHistory =
        userData &&
        userData.isAuthenticated &&
        (userData.isContributor === undefined || userData.isContributor);

    return (
        <div css={styles.titlebarContainer}>
            <div css={styles.titlebar}>
                <h1 css={styles.title}>{document.title}</h1>
                {showEditAndHistory && (
                    <EditAndHistoryButtons document={document} />
                )}
            </div>
        </div>
    );
}

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
                <LanguageMenu />
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

export default function Page() {
    const document = useContext(DocumentProvider.context);
    const ga = useContext(GAProvider.context);

    /*
     * Register an effect that runs every time we see a new document URL.
     * The effect sends a Google Analytics timing event to record how long
     * it took from the start of the navigation until the new document is
     * rendered. And then it turns off the loading indicator for the page
     *
     * Effects don't run during server-side-rendering, but that is fine
     * because we only want to send the GA event for client-side navigation.
     * Calling navigateRenderComplete() will have no effect if
     * navigateStart() was not previously called.
     */
    useEffect(() => {
        navigateRenderComplete(ga);

        // Client side navigation is typically so fast that the loading
        // animation might not even be noticed, so we artificially prolong
        // the effect with setTimeout()
        setTimeout(() => {
            DocumentProvider.setLoading(false);
        }, 200);
    }, [document && document.absoluteURL]);

    return (
        document && (
            <>
                <Header />
                <TaskCompletionSurvey />
                <Titlebar document={document} />
                <Breadcrumbs document={document} />
                <Content document={document} />
            </>
        )
    );
}

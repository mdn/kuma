// @flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import ClockIcon from './icons/clock.svg';
import ContributorsIcon from './icons/contributors.svg';
import DocumentProvider from './document-provider.jsx';
import gettext from './gettext.js';
import { Row, Strut } from './layout.jsx';
import Header from './header/header.jsx';

const strings = {
    relatedTopics: gettext('Related Topics'),
    contributorsToThisPage: gettext('Contributors to this page:'),
    lastUpdatedBy: gettext('Last updated by:')
};

const styles = {
    titlebar: css({
        backgroundColor: '#f5f9fa',
        padding: '12px 0 12px 32px'
    }),
    title: css({
        fontFamily:
            'x-locale-heading-primary, zillaslab, "Palatino", "Palatino Linotype", x-locale-heading-secondary, serif',
        fontSize: '2.8rem',
        margin: 0
    }),
    toc: css({
        color: '#fff',
        backgroundColor: '#222',
        padding: '8px 0 8px 32px',
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
    content: css({
        alignItems: 'start',
        padding: '30px 24px'
    }),
    article: css({
        flex: '0 0 74%',
        maxWidth: '74%',
        '& p': {
            maxWidth: '42rem'
        }
    }),
    sidebar: css({
        flex: '0 0 23%',
        maxWidth: '23%'
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

function Titlebar() {
    const documentData = useContext(DocumentProvider.context);

    return (
        documentData && (
            <Row css={styles.titlebar}>
                <h1 css={styles.title}>{documentData.title}</h1>
            </Row>
        )
    );
}

function TOC() {
    const documentData = useContext(DocumentProvider.context);

    return (
        documentData && (
            <Row
                css={styles.toc}
                dangerouslySetInnerHTML={{
                    __html: `<ol>${documentData.tocHTML}</ol>`
                }}
            />
        )
    );
}

function Sidebar() {
    const documentData = useContext(DocumentProvider.context);

    return (
        documentData && (
            <div css={styles.sidebar}>
                <Breadcrumbs />
                <Quicklinks />
            </div>
        )
    );
}

function Breadcrumbs() {
    const documentData = useContext(DocumentProvider.context);

    // The <span> elements below aren't needed except that the stylesheets
    // are set up to expect them.
    return (
        documentData && (
            <nav className="crumbs" role="navigation">
                <ol>
                    {documentData.parents.map(p => (
                        <li className="crumb" key={p.url}>
                            <a href={p.url}>
                                <span>{p.title}</span>
                            </a>
                        </li>
                    ))}
                    <li className="crumb">
                        <span>{documentData.title}</span>
                    </li>
                </ol>
            </nav>
        )
    );
}

function Quicklinks() {
    const documentData = useContext(DocumentProvider.context);
    return (
        documentData && (
            <div className="quick-links" css={styles.quicklinks}>
                <div className="quick-links-head">{strings.relatedTopics}</div>
                <div
                    dangerouslySetInnerHTML={{
                        __html: documentData.quickLinksHTML
                    }}
                />
            </div>
        )
    );
}

function Article() {
    const documentData = useContext(DocumentProvider.context);
    return (
        // The "text-content" class and "wikiArticle" id are required
        // because our stylesheets expect them and formatting isn't quite
        // right without them.
        documentData && (
            <div className="text-content" css={styles.article}>
                <article
                    id="wikiArticle"
                    dangerouslySetInnerHTML={{ __html: documentData.bodyHTML }}
                />
                <ArticleMetadata />
            </div>
        )
    );
}

function ArticleMetadata() {
    const documentData = useContext(DocumentProvider.context);
    return (
        documentData && (
            <div css={styles.metadata}>
                <div>
                    <ContributorsIcon css={styles.contributorsIcon} />{' '}
                    <strong>{strings.contributorsToThisPage}</strong>{' '}
                    {documentData.contributors.map((c, i) => (
                        <span key={c}>
                            {i > 0 && ', '}
                            <a
                                href={`/${
                                    documentData.localeFromURL
                                }/profiles/${c}`}
                                rel="nofollow"
                            >
                                {c}
                            </a>
                        </span>
                    ))}
                </div>
                <div>
                    <ClockIcon css={styles.clockIcon} />{' '}
                    <strong>{strings.lastUpdatedBy}</strong>{' '}
                    {documentData.lastModifiedBy}{' '}
                    <time dateTime={documentData.lastModified}>
                        {new Date(documentData.lastModified)
                            .toISOString()
                            .slice(0, -5)
                            .replace('T', ' ')}
                    </time>
                </div>
            </div>
        )
    );
}

export default function Page() {
    return (
        <div>
            <Header />
            <Titlebar />
            <TOC />
            <Row css={styles.content}>
                <Sidebar />
                <Strut width="3%" />
                <Article />
            </Row>
        </div>
    );
}

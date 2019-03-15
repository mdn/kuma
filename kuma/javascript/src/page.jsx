// @flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import DocumentProvider from './document-provider.jsx';
import gettext from './gettext.js';
import { Row, Strut } from './layout.jsx';
import Header from './header/header.jsx';

const strings = {
    relatedTopics: gettext('Related Topics')
};

const styles = {
    titlebar: css({
        backgroundColor: '#f5f9fa',
        padding: '16px 0 16px 32px'
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
        padding: '15px 0 15px 32px',
        '& li': {
            display: 'inline-block'
        },
        '& a': {
            color: '#83d0f2',
            paddingRight: 30,
            whiteSpace: 'nowrap',
            textDecoration: 'none',
            fontSize: '1rem'
        }
    }),
    content: css({
        alignItems: 'start',
        padding: '30px 24px'
    }),
    article: css({
        flex: 3,
        '& p': {
            maxWidth: '42rem'
        }
    }),
    sidebar: css({
        flex: 1
    }),
    breadcrumbs: css({}),
    quicklinks: css({})
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
        documentData && (
            <article
                className="text-content"
                css={styles.article}
                dangerouslySetInnerHTML={{ __html: documentData.bodyHTML }}
            />
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

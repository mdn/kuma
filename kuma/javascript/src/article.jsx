// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';
import { css } from '@emotion/core';

import { activateBCDTables } from './bcd.js';
import { addLiveExampleButtons } from './live-examples.js';
import { highlightSyntax } from './prism.js';
import * as InteractiveExamples from './interactive-examples.js';
import UserProvider from './user-provider.jsx';

import Contributors from './contributors.jsx';
import LastModifiedBy from './last-modified-by.jsx';
import sectionAnchor from './section-anchor.jsx';

import type { DocumentData } from './document.jsx';
type DocumentProps = {
    document: DocumentData
};

// A media query that identifies screens narrower than a tablet
const NARROW = '@media (max-width: 749px)';

const styles = {
    article: css({
        gridArea: 'main',
        boxSizing: 'border-box',
        width: '100%',
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
        },
        '& a.sectionLink': {
            fontSize: 24,
            textDecoration: 'none'
        },

        // Styles for BCD tables, overriding the stylesheets
        '& table.bc-table button.bc-history-link': {
            ':focus': {
                outline: '#83d0f2 solid 3px',
                outlineOffset: -3
            },
            ':hover': {
                backgroundColor: '#83d0f2 !important'
            }
        }
    }),
    metadata: css({
        marginTop: 32,
        fontSize: '0.88889rem',
        color: '#696969',
        '& div': {
            margin: '4px 0'
        }
    })
};

/* This is an effect function that runs every time the article is rendered.
   This is the React version of the pre-React code in
   kuma/static/js/components/local-anchor.js */
function addAnchors(article) {
    for (let heading of article.querySelectorAll('h2[id], h3[id]')) {
        // do not add the widget to headings that are hidden
        if (!heading.classList.contains('offscreen')) {
            /* we add the widget to a different place in the DOM
               for H2 elements than for H3 elements */
            if (heading.tagName === 'H2') {
                heading.insertAdjacentElement(
                    'beforeend',
                    sectionAnchor(heading)
                );
            } else {
                heading.insertAdjacentElement(
                    'afterend',
                    sectionAnchor(heading)
                );
            }
        }
    }
}

export default function Article({ document }: DocumentProps) {
    const article = useRef(null);
    const userData = useContext(UserProvider.context);

    // This is a one-time effect we need to call the first time an article
    // is rendered, to ensure that interactive examples resize themselves
    // if the browser width changes.
    useEffect(InteractiveExamples.makeResponsive, []);

    // Each time we display an article we need to patch it up
    // in various ways.
    useEffect(() => {
        let rootElement = article.current;
        if (rootElement) {
            InteractiveExamples.setLayout(rootElement);
            // Keep addLiveExampleButtons() before addAnchors() so the
            // example title doesn't end up with a link in it on codepen.
            addLiveExampleButtons(rootElement);
            addAnchors(rootElement);
            highlightSyntax(rootElement);
            activateBCDTables(rootElement);
        }
    }, [document]);

    useEffect(() => {
        let rootElement = article.current;
        if (rootElement) {
            // The reasons it might NOT exist is because perhaps it's not
            // loaded because a waffle flag tells it not to.
            if (window.activateBCDSignals) {
                window.activateBCDSignals(document.slug, document.locale);
            }
        }
    }, [document, userData]);

    const isArchive =
        document.slug === 'Archive' || document.slug.startsWith('Archive/');

    return (
        /*
         * The "text-content" class and "wikiArticle" id are required
         * because our stylesheets expect them and formatting isn't quite
         * right without them.
         */
        <div
            id="content"
            ref={article}
            className={
                isArchive ? 'text-content archive-content' : 'text-content'
            }
            css={styles.article}
        >
            <article
                id="wikiArticle"
                dangerouslySetInnerHTML={{ __html: document.bodyHTML }}
            />
            <ArticleMetadata document={document} />
        </div>
    );
}

function ArticleMetadata({ document }: DocumentProps) {
    const url = new URL(document.editURL);
    const profileBaseURL = `${url.protocol}//${url.host}/profiles/`;

    return (
        <div css={styles.metadata}>
            <Contributors
                contributors={document.contributors}
                profileBaseURL={profileBaseURL}
            />
            <LastModifiedBy
                lastModifiedBy={document.lastModifiedBy}
                lastModified={document.lastModified}
                profileBaseURL={profileBaseURL}
                documentLocale={document.locale}
            />
        </div>
    );
}

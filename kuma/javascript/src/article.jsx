// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';
import { css } from '@emotion/core';

import { activateBCDSignals, activateBCDTables } from './bcd.js';
import { addLiveExampleButtons } from './live-examples.js';
import { gettext } from './l10n.js';
import { highlightSyntax } from './prism.js';
import * as InteractiveExamples from './interactive-examples.js';
import TagsIcon from './icons/tags.svg';
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
    }),
    tags: css({
        display: 'inline',
        // Our main.css stylesheet has a ".text-content ul" style we need
        // to override with the !important below
        paddingLeft: '0px !important',

        // These tag styles also appear in search-results-page.jsx
        // We should probably keep the two designs in sync
        '& li': {
            display: 'inline-block',
            whiteSpace: 'nowrap',
            fontSize: 12,
            lineHeight: 1.2,
            backgroundColor: '#f5f9fa',
            border: 'solid 1px #dce3e5',
            borderRadius: 5,
            padding: '2px 4px',
            marginRight: 8
        }
    })
};

// This is an effect function that runs every time the article is rendered.
// This is the React version of the code in kuma/static/js/highlight.js
// which is used on the wiki domain
function highlightSections(article) {
    let sections = article.querySelectorAll('#wikiArticle h3, #wikiArticle h5');
    for (let section of sections) {
        section.classList.add('highlight-spanned');
        section.innerHTML = `<span class="highlight-span">${
            section.innerHTML
        }</span>`;
    }
}

// This is an effect function that runs every time the article is rendered.
// This is the React version of the pre-React code in
// kuma/static/js/components/local-anchor.js
function addAnchors(article) {
    for (let heading of article.querySelectorAll('h2[id], h3[id]')) {
        heading.insertAdjacentElement('beforeend', sectionAnchor(heading));
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
            highlightSections(rootElement);
            addAnchors(rootElement);
            highlightSyntax(rootElement);
            activateBCDTables(rootElement);
        }
    }, [document]);

    useEffect(() => {
        let rootElement = article.current;
        if (rootElement) {
            activateBCDSignals(
                rootElement,
                document.slug,
                document.locale,
                userData
            );
        }
    }, [document, userData]);

    return (
        /*
         * The "text-content" class and "wikiArticle" id are required
         * because our stylesheets expect them and formatting isn't quite
         * right without them.
         */
        <div
            id="content"
            ref={article}
            className="text-content"
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
            <div>
                <TagsIcon
                    css={styles.metadataIcon}
                    className="icon icon-tags"
                />{' '}
                <strong>{gettext('Tags:')}</strong>{' '}
                <ul css={styles.tags}>
                    {document.tags.map(c => (
                        <li key={c}>{c}</li>
                    ))}
                </ul>
            </div>
            <Contributors
                contributors={document.contributors}
                profileBaseURL={profileBaseURL}
            />
            <LastModifiedBy
                lastModifiedBy={document.lastModifiedBy}
                lastModified={document.lastModified}
                profileBaseURL={profileBaseURL}
            />
        </div>
    );
}

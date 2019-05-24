// @flow
import * as React from 'react';
import { useEffect, useRef } from 'react';
import { css } from '@emotion/core';

import ClockIcon from './icons/clock.svg';
import ContributorsIcon from './icons/contributors.svg';
import { getLocale, gettext } from './l10n.js';

import type { DocumentData } from './document-provider.jsx';
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
        },
        '& a.sectionLink': {
            fontSize: 24,
            textDecoration: 'none'
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
        let anchor = document.createElement('a');
        anchor.href = `#${heading.id}`;
        anchor.classList.add('sectionLink');
        anchor.textContent = ' \uD83D\uDD17'; // Unicode link emoji
        heading.insertAdjacentElement('beforeend', anchor);
    }
}

export default function Article({ document }: DocumentProps) {
    const article = useRef(null);
    useEffect(() => article.current && highlightSections(article.current));
    useEffect(() => article.current && addAnchors(article.current));

    return (
        /*
         * The "text-content" class and "wikiArticle" id are required
         * because our stylesheets expect them and formatting isn't quite
         * right without them.
         */
        <div ref={article} className="text-content" css={styles.article}>
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

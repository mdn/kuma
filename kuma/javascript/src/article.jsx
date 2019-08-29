// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';

import { activateBCDSignals, activateBCDTables } from './bcd.js';
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

/* This is an effect function that runs every time the article is rendered.
   This is the React version of the pre-React code in
   kuma/static/js/components/local-anchor.js */
function addAnchors(article) {
    /**
     * As of Aug 30, 2019 the body HTML is now rendered with anchor links
     * the HTML returned from the document JSON API. This depends on the
     * document having had a chance to re-render from that date onwards.
     * Basically, if the HTML appears to have `a.section-link` tags in it,
     * bail early and don't bother doing this with client-side JavaScript.
     * Take stock at the end of 2019 to see if all pages have been
     * re-generated, if so, delete this whole function.
     * See https://github.com/mozilla/kuma/issues/5718
     */
    if (article.querySelector('a.section-link')) {
        return;
    }
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
            activateBCDSignals(document.slug, document.locale, userData);
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
                isArchive
                    ? 'article text-content archive-content'
                    : 'article text-content'
            }
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
        <div className="metadata">
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

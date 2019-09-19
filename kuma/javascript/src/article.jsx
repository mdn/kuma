// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';

import { activateBCDSignals, activateBCDTables } from './bcd.js';
import { addLiveExampleButtons } from './live-examples.js';
import { getLocale, gettext } from './l10n.js';
import { highlightSyntax } from './prism.js';
import * as InteractiveExamples from './interactive-examples.js';
import UserProvider from './user-provider.jsx';

import LastModified from './last-modified.jsx';
import type { DocumentData } from './document.jsx';

type DocumentProps = {
    document: DocumentData
};

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
    const locale = getLocale();

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
            {document.locale !== locale && (
                <div className="warning">
                    <p>
                        <bdi>
                            {gettext(
                                'You’re reading the English version of this content since no translation exists yet for this locale.'
                            )}
                            &nbsp;
                            <a href={document.translateURL} rel="nofollow">
                                {gettext('Help us translate this article!')}
                            </a>
                        </bdi>
                    </p>
                </div>
            )}
            <article
                id="wikiArticle"
                dangerouslySetInnerHTML={{ __html: document.bodyHTML }}
            />
            <ArticleMetadata document={document} />
        </div>
    );
}

function ArticleMetadata({ document }: DocumentProps) {
    const wikiRevisionHistoryURL = document.wikiURL + '$history';
    return (
        <div className="metadata">
            <LastModified
                lastModified={document.lastModified}
                wikiRevisionHistoryURL={wikiRevisionHistoryURL}
                documentLocale={document.locale}
            />
        </div>
    );
}

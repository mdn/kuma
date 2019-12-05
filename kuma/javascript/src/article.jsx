// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';

import { activateBCDTables } from './bcd.js';
import { addLiveExampleButtons } from './live-examples.js';
import { getLocale, gettext } from './l10n.js';
import { highlightSyntax } from './prism.js';
import * as InteractiveExamples from './interactive-examples.js';
import UserProvider from './user-provider.jsx';
import GAProvider from './ga-provider.jsx';

import LastModified from './last-modified.jsx';
import type { DocumentData } from './document.jsx';

type DocumentProps = {
    document: DocumentData
};

function TranslationStatus({
    document: { translationStatus, translateURL }
}: DocumentProps) {
    let content;

    if (translationStatus === 'in-progress') {
        content = gettext('This translation is in progress.');
    } else if (translationStatus === 'outdated') {
        content = (
            <>
                {gettext(
                    'You’re reading the English version of this content since no translation exists yet for this locale.'
                )}
                &nbsp;
                <a href={translateURL} rel="nofollow">
                    {gettext('Help us translate this article!')}
                </a>
            </>
        );
    }

    if (translationStatus == null || !content) {
        return null;
    }

    return (
        <p className="overheadIndicator translationInProgress">
            <bdi>{content}</bdi>
        </p>
    );
}

export default function Article({ document }: DocumentProps) {
    const article = useRef(null);
    const userData = useContext(UserProvider.context);
    const ga = useContext(GAProvider.context);

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
            try {
                addLiveExampleButtons(rootElement);
            } catch (error) {
                console.error(error);
                ga('send', {
                    hitType: 'event',
                    eventCategory: 'article-effect-error',
                    eventAction: 'addLiveExampleButtons',
                    eventLabel: error.toString()
                });
            }
            highlightSyntax(rootElement);
            try {
                activateBCDTables(rootElement);
            } catch (error) {
                console.error(error);
                ga('send', {
                    hitType: 'event',
                    eventCategory: 'article-effect-error',
                    eventAction: 'activateBCDTables',
                    eventLabel: error.toString()
                });
            }
        }
    }, [document, ga]);

    useEffect(() => {
        let rootElement = article.current;
        if (rootElement) {
            // The reasons it might NOT exist is because perhaps it's not
            // loaded because a setting tells it not to.
            if (window.activateBCDSignals) {
                try {
                    window.activateBCDSignals(document.slug, document.locale);
                } catch (error) {
                    console.error(error);
                    ga('send', {
                        hitType: 'event',
                        eventCategory: 'article-effect-error',
                        eventAction: 'activateBCDSignals',
                        eventLabel: error.toString()
                    });
                }
            }
        }
    }, [document, userData, ga]);

    const isArchive =
        document.slug === 'Archive' || document.slug.startsWith('Archive/');
    const locale = getLocale();

    useEffect(() => {
        if (document.locale !== locale) {
            ga('send', {
                hitType: 'event',
                eventCategory: 'Translation Pending',
                eventAction: 'displayed',
                eventLabel: ''
            });
        }
    }, [document, locale, ga]);

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
            <TranslationStatus document={document} />
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

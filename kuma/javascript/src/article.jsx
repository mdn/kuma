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
    document: DocumentData,
};

function TranslationStatus({
    document: { translationStatus, editURL },
}: DocumentProps) {
    let content;

    if (translationStatus === 'in-progress') {
        content = gettext('This translation is in progress.');
    } else if (translationStatus === 'outdated') {
        content = (
            <>
                {gettext('This translation is incomplete.')}
                &nbsp;
                <a href={editURL} rel="nofollow">
                    {gettext('Please help translate this article from English')}
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
                    eventLabel: error.toString(),
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
                    eventLabel: error.toString(),
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
                        eventLabel: error.toString(),
                    });
                }
            }
        }
    }, [document, userData, ga]);

    /** Any link inside the article that matches `a.new` means it's a
     * wiki page that hasn't yet been created. Clicking on it will
     * 404, if you're on the read-only site. If you're viewing HTML
     * like that on the Wiki and click it, it will take you to the
     * form to *create* the page. Disable all of that here in the read-only
     * site.
     *
     * The reason we're only going ahead with this mutation for 'en-US' documents
     * is that many non-en-US documents might have links to slugs that don't
     * exist in *this* locale but will fall back on the en-US. For example,
     * a link like this:
     *
     *     <a href="/pt-BR/docs/Foo/bar" class="new">Foo bar</a>
     *
     * ...might actually work. Even if there is no document with that locale +
     * slug combination.
     */
    useEffect(() => {
        let rootElement = article.current;
        if (rootElement && document.locale === 'en-US') {
            for (let link of rootElement.querySelectorAll('a.new')) {
                // Makes it not be clickable and no "pointer" cursor when
                // hovering. Better than clicking on it and being
                // disappointed.
                link.removeAttribute('href');
                if (!link.title) {
                    link.title = gettext('Page has not yet been created.');
                }
            }
        }
    }, [document]);

    const isArchive =
        document.slug === 'Archive' || document.slug.startsWith('Archive/');
    const locale = getLocale();

    useEffect(() => {
        if (document.locale !== locale) {
            ga('send', {
                hitType: 'event',
                eventCategory: 'Translation Pending',
                eventAction: 'displayed',
                eventLabel: '',
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

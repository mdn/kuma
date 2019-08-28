// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';

import { activateBCDSignals, activateBCDTables } from './bcd.js';
import { addLiveExampleButtons } from './live-examples.js';
import { gettext } from './l10n.js';
import { highlightSyntax } from './prism.js';
import * as InteractiveExamples from './interactive-examples.js';
import UserProvider from './user-provider.jsx';

import Contributors from './contributors.jsx';
import LastModifiedBy from './last-modified-by.jsx';

import type { DocumentData } from './document.jsx';
type DocumentProps = {
    document: DocumentData
};

let processed = false;

function insertSectionLinks(bodyHTML) {
    const sectionHeadingsRegExp = /(<h2 id.+|<h3 id.+)/g;
    const idTextRegExp = /(?:id=")(.+?)(?:")/;
    const innerTextRegExp = /(?:">)(.+)(?:<\/)/;
    const anchorIcon =
        '<svg class="icon icon-link" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M326.612 185.391c59.747 59.809 58.927 155.698.36 214.59-.11.12-.24.25-.36.37l-67.2 67.2c-59.27 59.27-155.699 59.262-214.96 0-59.27-59.26-59.27-155.7 0-214.96l37.106-37.106c9.84-9.84 26.786-3.3 27.294 10.606.648 17.722 3.826 35.527 9.69 52.721 1.986 5.822.567 12.262-3.783 16.612l-13.087 13.087c-28.026 28.026-28.905 73.66-1.155 101.96 28.024 28.579 74.086 28.749 102.325.51l67.2-67.19c28.191-28.191 28.073-73.757 0-101.83-3.701-3.694-7.429-6.564-10.341-8.569a16.037 16.037 0 0 1-6.947-12.606c-.396-10.567 3.348-21.456 11.698-29.806l21.054-21.055c5.521-5.521 14.182-6.199 20.584-1.731a152.482 152.482 0 0 1 20.522 17.197zM467.547 44.449c-59.261-59.262-155.69-59.27-214.96 0l-67.2 67.2c-.12.12-.25.25-.36.37-58.566 58.892-59.387 154.781.36 214.59a152.454 152.454 0 0 0 20.521 17.196c6.402 4.468 15.064 3.789 20.584-1.731l21.054-21.055c8.35-8.35 12.094-19.239 11.698-29.806a16.037 16.037 0 0 0-6.947-12.606c-2.912-2.005-6.64-4.875-10.341-8.569-28.073-28.073-28.191-73.639 0-101.83l67.2-67.19c28.239-28.239 74.3-28.069 102.325.51 27.75 28.3 26.872 73.934-1.155 101.96l-13.087 13.087c-4.35 4.35-5.769 10.79-3.783 16.612 5.864 17.194 9.042 34.999 9.69 52.721.509 13.906 17.454 20.446 27.294 10.606l37.106-37.106c59.271-59.259 59.271-155.699.001-214.959z"/></svg>';
    let resultsArray = [];

    while ((resultsArray = sectionHeadingsRegExp.exec(bodyHTML)) !== null) {
        let heading = resultsArray[0];
        let headingId = heading.match(idTextRegExp)[1];
        let innerText = heading.match(innerTextRegExp)[1];

        if (heading.indexOf('offscreen') === -1) {
            /* we add the widget to a different place in the DOM
               for H2 elements than for H3 elements */
            if (heading.indexOf('h2') > -1) {
                bodyHTML = bodyHTML.replace(
                    resultsArray[0],
                    `<h2 id="${headingId}">${innerText}<a class="section-link" href="#${headingId}" aria-label="${gettext(
                        'Link to'
                    )} ${innerText}">${anchorIcon}</a></h2>`
                );
            } else {
                bodyHTML = bodyHTML.replace(
                    resultsArray[0],
                    `<h3 id="${headingId}">${innerText}</h3><a class="section-link" href="#${headingId}" aria-label="${gettext(
                        'Link to'
                    )} ${innerText}">${anchorIcon}</a>`
                );
            }
        }
    }
    return bodyHTML;
}

export default function Article({ document }: DocumentProps) {
    const article = useRef(null);
    const userData = useContext(UserProvider.context);

    console.log('Article');
    if (!processed) {
        document.bodyHTML = insertSectionLinks(document.bodyHTML);
        processed = true;
    }

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
            //addAnchors(rootElement);
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

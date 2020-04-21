// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';

import GAProvider from './ga-provider.jsx';
import { gettext } from './l10n.js';

import Caret from './icons/caret-down.svg';

type Props = {
    html: string,
};

export default function TOC({ html }: Props) {
    const ga = useContext(GAProvider.context);
    const documentTOCRef = useRef(null);
    const tocRef = useRef(null);

    /**
     * Send a signal to GA when the user clicks on one of links
     * in the table of contents
     * @param {Object} event - The event object that was triggered
     */
    function sendTOCClicks(event: MouseEvent) {
        if (event.target instanceof HTMLAnchorElement) {
            const action = event.target.textContent;
            const label = new URL(event.target.href).hash;

            ga('send', {
                hitType: 'event',
                eventCategory: 'MozMenu',
                eventAction: action,
                eventLabel: label,
            });
        }
    }

    /**
     * Show or hide the table of contents on
     * mobile devices
     */
    function toggleTOC() {
        const toc = tocRef.current;
        if (toc) {
            toc.classList.toggle('show-toc');
        }
    }

    useEffect(() => {
        const documentToc = documentTOCRef.current;

        if (documentToc) {
            documentToc.addEventListener('click', sendTOCClicks);
        }

        return () => {
            if (documentToc) {
                documentToc.removeEventListener('click', sendTOCClicks);
            }
        };
    });

    return (
        <aside className="document-toc-container">
            <section className="document-toc" ref={documentTOCRef}>
                <header>
                    <h2>{gettext('On this Page')}</h2>
                    <button
                        type="button"
                        className="toc-trigger-mobile"
                        onClick={toggleTOC}
                    >
                        {gettext('Jump to section')}
                        <Caret />
                    </button>
                </header>
                <ul
                    ref={tocRef}
                    dangerouslySetInnerHTML={{
                        __html: html,
                    }}
                />
            </section>
        </aside>
    );
}
